"""CLI del agente: generar, revisar y publicar."""
from __future__ import annotations

import logging
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from social_agent.brand import load_brand_profile
from social_agent.content import ContentGenerator
from social_agent.models import Draft, DraftStatus, Platform
from social_agent.publishers import PublishError, build_publishers
from social_agent.settings import get_settings
from social_agent.store import DraftQueue

app = typer.Typer(
    help="Agente de publicacion semanal para cuperinox.es", no_args_is_help=True
)
console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_STATUS_COLOR = {
    DraftStatus.PENDING: "yellow",
    DraftStatus.APPROVED: "cyan",
    DraftStatus.REJECTED: "red",
    DraftStatus.PUBLISHED: "green",
    DraftStatus.FAILED: "bright_red",
}


def _queue() -> DraftQueue:
    return DraftQueue(get_settings().database_path)


def _show(draft: Draft) -> None:
    header = (
        f"[bold]#{draft.id}[/bold] {draft.platform.value} · {draft.topic} · "
        f"[{_STATUS_COLOR[draft.status]}]{draft.status.value}[/]"
    )
    lines = [draft.rendered(), "", f"[dim]{len(draft.rendered())} caracteres[/dim]"]
    if draft.image_url:
        lines.append(f"[dim]imagen: {draft.image_url}[/dim]")
    elif draft.platform is Platform.INSTAGRAM:
        lines.append("[bright_red]falta imagen[/bright_red]")
    if draft.status is DraftStatus.PENDING and draft.error:
        lines.append(f"[dim]foto sugerida: {draft.error}[/dim]")
    console.print(Panel("\n".join(lines), title=header, expand=False))


@app.command()
def generate(
    platform: list[str] = typer.Option(
        ["linkedin", "instagram"], "--platform", "-p", help="Plataformas a generar"
    ),
    briefing: str = typer.Option(
        "", "--briefing", "-b", help="Material de partida de esta semana"
    ),
    week: int = typer.Option(0, "--week", "-w", help="Semana ISO (0 = actual)"),
) -> None:
    """Genera los borradores de la semana y los deja pendientes de revision."""
    settings = get_settings()
    brand = load_brand_profile(settings.brand_profile_path)
    generator = ContentGenerator(settings, brand)
    platforms = [Platform(p) for p in platform]
    iso_week = week or datetime.now().isocalendar().week

    with _queue() as queue:
        for p in platforms:
            draft = generator.generate(p, week=iso_week, briefing=briefing or None)
            queue.add(draft)
            _show(draft)

    console.print(
        "\n[bold]Revisalos con[/bold] `social review` "
        "y apruebalos con `social approve <id>`."
    )


@app.command(name="list")
def list_drafts(
    status: str = typer.Option("", "--status", "-s"),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Lista los borradores de la cola."""
    with _queue() as queue:
        drafts = queue.list(
            status=DraftStatus(status) if status else None, limit=limit
        )

    table = Table(show_header=True, header_style="bold")
    for column in ("ID", "Plataforma", "Estado", "Tema", "Creado"):
        table.add_column(column)
    for d in drafts:
        table.add_row(
            str(d.id),
            d.platform.value,
            f"[{_STATUS_COLOR[d.status]}]{d.status.value}[/]",
            d.topic[:45],
            d.created_at.strftime("%Y-%m-%d %H:%M"),
        )
    console.print(table)


@app.command()
def review() -> None:
    """Muestra al completo todo lo que esta pendiente de revision."""
    with _queue() as queue:
        drafts = queue.list(status=DraftStatus.PENDING)
    if not drafts:
        console.print("[green]No hay nada pendiente de revisar.[/green]")
        return
    for d in drafts:
        _show(d)


@app.command()
def approve(draft_id: int) -> None:
    """Aprueba un borrador para su publicacion."""
    with _queue() as queue:
        draft = queue.get(draft_id)
        if not draft:
            raise typer.BadParameter(f"No existe el borrador {draft_id}")
        problems = draft.validation_errors()
        if problems:
            console.print("[bright_red]No se puede aprobar:[/bright_red]")
            for p in problems:
                console.print(f"  - {p}")
            raise typer.Exit(code=1)
        queue.set_status(draft_id, DraftStatus.APPROVED)
    console.print(f"[cyan]Borrador {draft_id} aprobado.[/cyan]")


@app.command()
def reject(draft_id: int, reason: str = typer.Option("", "--reason", "-r")) -> None:
    """Descarta un borrador."""
    with _queue() as queue:
        queue.set_status(draft_id, DraftStatus.REJECTED, error=reason or None)
    console.print(f"[red]Borrador {draft_id} descartado.[/red]")


@app.command()
def image(draft_id: int, url: str) -> None:
    """Asocia una imagen (URL publica) a un borrador."""
    with _queue() as queue:
        queue.set_image(draft_id, url)
    console.print(f"Imagen asociada al borrador {draft_id}.")


@app.command()
def edit(draft_id: int, body: str) -> None:
    """Reemplaza el cuerpo de un borrador."""
    with _queue() as queue:
        queue.update_body(draft_id, body)
        draft = queue.get(draft_id)
    if draft:
        _show(draft)


@app.command()
def publish(
    draft_id: int = typer.Option(0, "--id", help="Publica solo este borrador"),
) -> None:
    """Publica los borradores aprobados. Nada que no este APPROVED se toca."""
    settings = get_settings()
    publishers = build_publishers(settings)

    with _queue() as queue:
        drafts = (
            [d for d in [queue.get(draft_id)] if d]
            if draft_id
            else queue.list(status=DraftStatus.APPROVED, limit=100)
        )
        drafts = [d for d in drafts if d.status is DraftStatus.APPROVED]

        if not drafts:
            console.print("[yellow]No hay borradores aprobados.[/yellow]")
            return

        for draft in drafts:
            publisher = publishers.get(draft.platform)
            if publisher is None:
                console.print(
                    f"[yellow]#{draft.id}: {draft.platform.value} sin credenciales, "
                    "se omite.[/yellow]"
                )
                continue

            if settings.dry_run:
                console.print(f"[dim]DRY RUN #{draft.id} -> {draft.platform.value}[/dim]")
                _show(draft)
                continue

            try:
                result = publisher.publish(draft)
            except PublishError as exc:
                queue.set_status(draft.id, DraftStatus.FAILED, error=str(exc))
                console.print(f"[bright_red]#{draft.id} fallo:[/bright_red] {exc}")
                continue

            queue.set_status(
                draft.id, DraftStatus.PUBLISHED, remote_id=result.remote_id
            )
            console.print(
                f"[green]#{draft.id} publicado[/green] {result.url or result.remote_id}"
            )


@app.command()
def status() -> None:
    """Resumen de la cola y de las credenciales configuradas."""
    settings = get_settings()
    with _queue() as queue:
        counts = queue.counts_by_status()

    table = Table(title="Cola", show_header=True, header_style="bold")
    table.add_column("Estado")
    table.add_column("Nº", justify="right")
    for s in DraftStatus:
        table.add_row(
            f"[{_STATUS_COLOR[s]}]{s.value}[/]", str(counts.get(s.value, 0))
        )
    console.print(table)

    configured = build_publishers(settings)
    for p in Platform:
        mark = "[green]ok[/green]" if p in configured else "[red]sin configurar[/red]"
        console.print(f"{p.value}: {mark}")
    if settings.dry_run:
        console.print("[yellow]DRY_RUN activo: no se publicara nada.[/yellow]")


if __name__ == "__main__":
    app()
