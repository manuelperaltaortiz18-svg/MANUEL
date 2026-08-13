<?php
/**
 * Plugin Name: Maestros del Corte — Grabado personalizado
 * Description: Añade grabado personalizado sobre hoja de acero a los productos que lo permitan, con recargo configurable por producto.
 * Version: 1.0.0
 * Requires at least: 6.5
 * Requires PHP: 7.4
 * Author: Cuperinox
 * Text Domain: mdc-grabado
 * License: GPL-2.0-or-later
 *
 * Va como plugin y no dentro del tema a propósito: si algún día cambiáis
 * de tema, los pedidos con grabado siguen funcionando.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Longitud máxima del texto grabado. Limitada por el ancho de la hoja. */
const MDC_GRABADO_MAX_CARACTERES = 20;

/* ==================================================================== *
 * Administración: opciones por producto
 * ==================================================================== */

/**
 * Campos "admite grabado" y "recargo" en la pestaña General del producto.
 */
function mdc_grabado_campos_producto() {
	woocommerce_wp_checkbox(
		array(
			'id'          => '_mdc_grabado_activo',
			'label'       => __( 'Admite grabado', 'mdc-grabado' ),
			'description' => __( 'Solo para productos con hoja de acero. Las bases de madera no admiten grabado.', 'mdc-grabado' ),
		)
	);

	woocommerce_wp_text_input(
		array(
			'id'          => '_mdc_grabado_precio',
			'label'       => sprintf( __( 'Recargo por grabado (%s)', 'mdc-grabado' ), get_woocommerce_currency_symbol() ),
			'description' => __( 'Déjalo vacío o a 0 para ofrecer el grabado sin coste.', 'mdc-grabado' ),
			'desc_tip'    => true,
			'data_type'   => 'price',
		)
	);
}
add_action( 'woocommerce_product_options_general_product_data', 'mdc_grabado_campos_producto' );

/**
 * Guarda las opciones del producto.
 */
function mdc_grabado_guardar_campos( $product ) {
	// WooCommerce ya ha verificado el nonce del formulario de producto
	// antes de disparar este hook.
	// phpcs:disable WordPress.Security.NonceVerification.Missing
	$activo = isset( $_POST['_mdc_grabado_activo'] ) ? 'yes' : 'no';
	$precio = isset( $_POST['_mdc_grabado_precio'] )
		? wc_format_decimal( wp_unslash( $_POST['_mdc_grabado_precio'] ) )
		: '';
	// phpcs:enable WordPress.Security.NonceVerification.Missing

	$product->update_meta_data( '_mdc_grabado_activo', $activo );
	$product->update_meta_data( '_mdc_grabado_precio', $precio );
}
add_action( 'woocommerce_admin_process_product_object', 'mdc_grabado_guardar_campos' );

/* ==================================================================== *
 * Utilidades
 * ==================================================================== */

/**
 * ¿Este producto admite grabado?
 *
 * @param int $product_id ID del producto.
 * @return bool
 */
function mdc_grabado_disponible( $product_id ) {
	$product = wc_get_product( $product_id );

	if ( ! $product ) {
		return false;
	}

	// En una variación, la configuración vive en el producto padre.
	if ( $product->is_type( 'variation' ) ) {
		$product = wc_get_product( $product->get_parent_id() );

		if ( ! $product ) {
			return false;
		}
	}

	return 'yes' === $product->get_meta( '_mdc_grabado_activo' );
}

/**
 * Recargo del grabado para un producto.
 *
 * @param int $product_id ID del producto.
 * @return float
 */
function mdc_grabado_precio( $product_id ) {
	$product = wc_get_product( $product_id );

	if ( ! $product ) {
		return 0.0;
	}

	if ( $product->is_type( 'variation' ) ) {
		$product = wc_get_product( $product->get_parent_id() );

		if ( ! $product ) {
			return 0.0;
		}
	}

	return (float) $product->get_meta( '_mdc_grabado_precio' );
}

/**
 * Normaliza el texto grabado.
 *
 * Se permiten letras (con acentos y ñ), números, espacios y unos pocos
 * signos. Todo lo demás se descarta porque no se puede grabar limpio.
 *
 * @param string $texto Texto en bruto.
 * @return string
 */
function mdc_grabado_sanear( $texto ) {
	$texto = sanitize_text_field( $texto );
	$texto = preg_replace( '/[^\p{L}\p{N} .\'&-]/u', '', $texto );
	$texto = trim( preg_replace( '/\s+/u', ' ', $texto ) );

	return function_exists( 'mb_substr' )
		? mb_substr( $texto, 0, MDC_GRABADO_MAX_CARACTERES )
		: substr( $texto, 0, MDC_GRABADO_MAX_CARACTERES );
}

/* ==================================================================== *
 * Ficha de producto
 * ==================================================================== */

/**
 * Campo de grabado dentro del formulario de compra.
 */
function mdc_grabado_campo_ficha() {
	global $product;

	if ( ! $product || ! mdc_grabado_disponible( $product->get_id() ) ) {
		return;
	}

	$precio = mdc_grabado_precio( $product->get_id() );

	$etiqueta = $precio > 0
		/* translators: %s: importe del recargo ya formateado. */
		? sprintf( __( 'Grabado personalizado (+%s)', 'mdc-grabado' ), wp_strip_all_tags( wc_price( $precio ) ) )
		: __( 'Grabado personalizado (incluido)', 'mdc-grabado' );

	?>
	<div class="mdc-grabado">
		<label class="mdc-grabado__label" for="mdc_grabado_texto">
			<?php echo esc_html( $etiqueta ); ?>
		</label>

		<input
			type="text"
			id="mdc_grabado_texto"
			name="mdc_grabado_texto"
			class="mdc-grabado__input"
			maxlength="<?php echo esc_attr( MDC_GRABADO_MAX_CARACTERES ); ?>"
			placeholder="<?php esc_attr_e( 'Nombre, fecha o empresa', 'mdc-grabado' ); ?>"
			value=""
		/>

		<p class="mdc-grabado__ayuda">
			<?php
			printf(
				/* translators: %d: número máximo de caracteres. */
				esc_html__( 'Máximo %d caracteres. Se graba sobre la hoja de acero. Déjalo vacío si no quieres grabado.', 'mdc-grabado' ),
				(int) MDC_GRABADO_MAX_CARACTERES
			);
			?>
		</p>

		<p class="mdc-grabado__aviso">
			<?php esc_html_e( 'Los productos grabados son personalizados y no admiten devolución.', 'mdc-grabado' ); ?>
		</p>
	</div>
	<?php
}
add_action( 'woocommerce_before_add_to_cart_button', 'mdc_grabado_campo_ficha', 10 );

/**
 * Estilos del campo. Son cuatro reglas: no merece un archivo aparte.
 */
function mdc_grabado_estilos() {
	if ( ! function_exists( 'is_product' ) || ! is_product() ) {
		return;
	}

	$css = '
	.mdc-grabado{margin:0 0 1.5rem;padding:1.25rem;border:1px solid var(--wp--preset--color--line,#DCE1E9);border-radius:2px;background:var(--wp--preset--color--surface,#ECEFF4)}
	.mdc-grabado__label{display:block;margin-bottom:.6rem;font-size:.75rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase}
	.mdc-grabado__input{width:100%;padding:.85rem 1rem;border:1px solid var(--wp--preset--color--line,#DCE1E9);border-radius:2px;background:#fff;font-size:1rem}
	.mdc-grabado__input:focus{border-color:var(--wp--preset--color--accent,#153E6E);outline:2px solid rgba(21,62,110,.18);outline-offset:1px}
	.mdc-grabado__ayuda,.mdc-grabado__aviso{margin:.6rem 0 0;font-size:.8125rem;color:var(--wp--preset--color--contrast-soft,#5A616E)}
	.mdc-grabado__aviso{font-style:italic}
	';

	wp_register_style( 'mdc-grabado', false, array(), '1.0.0' );
	wp_enqueue_style( 'mdc-grabado' );
	wp_add_inline_style( 'mdc-grabado', $css );
}
add_action( 'wp_enqueue_scripts', 'mdc_grabado_estilos' );

/* ==================================================================== *
 * Carrito
 * ==================================================================== */

/**
 * Rechaza el texto si trae caracteres que no se pueden grabar.
 *
 * @param bool $pasa       Resultado acumulado de la validación.
 * @param int  $product_id ID del producto.
 * @return bool
 */
function mdc_grabado_validar( $pasa, $product_id ) {
	// phpcs:ignore WordPress.Security.NonceVerification.Missing -- Woo valida el formulario de añadir al carrito.
	$bruto = isset( $_POST['mdc_grabado_texto'] ) ? wp_unslash( $_POST['mdc_grabado_texto'] ) : '';

	if ( '' === trim( $bruto ) ) {
		return $pasa;
	}

	if ( ! mdc_grabado_disponible( $product_id ) ) {
		return $pasa;
	}

	if ( '' === mdc_grabado_sanear( $bruto ) ) {
		wc_add_notice(
			__( 'El texto del grabado solo admite letras, números y los signos . \' & -', 'mdc-grabado' ),
			'error'
		);
		return false;
	}

	return $pasa;
}
add_filter( 'woocommerce_add_to_cart_validation', 'mdc_grabado_validar', 10, 2 );

/**
 * Adjunta el texto a la línea de carrito.
 *
 * @param array $datos      Datos de la línea.
 * @param int   $product_id ID del producto.
 * @return array
 */
function mdc_grabado_datos_carrito( $datos, $product_id ) {
	// phpcs:ignore WordPress.Security.NonceVerification.Missing -- Woo valida el formulario de añadir al carrito.
	$bruto = isset( $_POST['mdc_grabado_texto'] ) ? wp_unslash( $_POST['mdc_grabado_texto'] ) : '';
	$texto = mdc_grabado_sanear( $bruto );

	if ( '' === $texto || ! mdc_grabado_disponible( $product_id ) ) {
		return $datos;
	}

	$datos['mdc_grabado'] = array(
		'texto'   => $texto,
		'recargo' => mdc_grabado_precio( $product_id ),
	);

	// Sin esto, dos unidades del mismo cuchillo con grabados distintos se
	// fusionarían en una sola línea y se perdería uno de los textos.
	$datos['unique_key'] = md5( $texto . '|' . $product_id . '|' . microtime() );

	return $datos;
}
add_filter( 'woocommerce_add_cart_item_data', 'mdc_grabado_datos_carrito', 10, 2 );

/**
 * Muestra el grabado en carrito y checkout.
 *
 * @param array $items Metadatos visibles de la línea.
 * @param array $linea Línea de carrito.
 * @return array
 */
function mdc_grabado_mostrar_carrito( $items, $linea ) {
	if ( empty( $linea['mdc_grabado']['texto'] ) ) {
		return $items;
	}

	$items[] = array(
		'key'   => __( 'Grabado', 'mdc-grabado' ),
		'value' => esc_html( $linea['mdc_grabado']['texto'] ),
	);

	return $items;
}
add_filter( 'woocommerce_get_item_data', 'mdc_grabado_mostrar_carrito', 10, 2 );

/**
 * Suma el recargo al precio de la línea.
 *
 * @param WC_Cart $cart Carrito.
 */
function mdc_grabado_aplicar_recargo( $cart ) {
	if ( is_admin() && ! defined( 'DOING_AJAX' ) ) {
		return;
	}

	// WooCommerce puede disparar este hook más de una vez por petición;
	// sin esta guarda el recargo se sumaría de forma acumulativa.
	if ( did_action( 'woocommerce_before_calculate_totals' ) > 1 ) {
		return;
	}

	foreach ( $cart->get_cart() as $linea ) {
		if ( empty( $linea['mdc_grabado'] ) ) {
			continue;
		}

		$recargo = (float) $linea['mdc_grabado']['recargo'];

		if ( $recargo <= 0 ) {
			continue;
		}

		$producto = $linea['data'];
		$producto->set_price( (float) $producto->get_price( 'edit' ) + $recargo );
	}
}
add_action( 'woocommerce_before_calculate_totals', 'mdc_grabado_aplicar_recargo', 20 );

/* ==================================================================== *
 * Pedido
 * ==================================================================== */

/**
 * Deja el grabado grabado (nunca mejor dicho) en la línea de pedido, para
 * que taller y cliente vean lo mismo en el email, el albarán y el admin.
 *
 * @param WC_Order_Item_Product $item  Línea de pedido.
 * @param string                $key   Clave de la línea de carrito.
 * @param array                 $linea Línea de carrito.
 */
function mdc_grabado_guardar_en_pedido( $item, $key, $linea ) {
	if ( empty( $linea['mdc_grabado']['texto'] ) ) {
		return;
	}

	$item->add_meta_data( __( 'Grabado', 'mdc-grabado' ), $linea['mdc_grabado']['texto'], true );
}
add_action( 'woocommerce_checkout_create_order_line_item', 'mdc_grabado_guardar_en_pedido', 10, 3 );
