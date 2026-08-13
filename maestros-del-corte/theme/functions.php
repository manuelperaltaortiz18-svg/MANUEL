<?php
/**
 * Maestros del Corte — arranque del tema.
 *
 * @package maestros-del-corte
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'MDC_VERSION', '1.0.0' );

/**
 * Soportes del tema.
 */
function mdc_setup() {
	load_theme_textdomain( 'maestros-del-corte', get_template_directory() . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );

	// WooCommerce. La galería con zoom y lightbox es lo que hace que un
	// producto de 200 € se pueda inspeccionar antes de comprar.
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
}
add_action( 'after_setup_theme', 'mdc_setup' );

/**
 * Hojas de estilo.
 */
function mdc_enqueue_assets() {
	wp_enqueue_style(
		'mdc-style',
		get_template_directory_uri() . '/style.css',
		array(),
		MDC_VERSION
	);

	if ( class_exists( 'WooCommerce' ) ) {
		wp_enqueue_style(
			'mdc-woocommerce',
			get_template_directory_uri() . '/assets/css/woocommerce.css',
			array( 'mdc-style' ),
			MDC_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'mdc_enqueue_assets' );

/**
 * Categoría propia para los patrones del tema, para que en el editor
 * aparezcan agrupados y sean fáciles de encontrar.
 */
function mdc_register_pattern_category() {
	register_block_pattern_category(
		'maestros-del-corte',
		array( 'label' => __( 'Maestros del Corte', 'maestros-del-corte' ) )
	);
}
add_action( 'init', 'mdc_register_pattern_category' );

/**
 * Productos por página en el catálogo.
 *
 * Con catálogo corto conviene que quepa todo en una pantalla o dos: cada
 * clic de paginación es una fuga.
 */
function mdc_products_per_page() {
	return 24;
}
add_filter( 'loop_shop_per_page', 'mdc_products_per_page', 20 );

/**
 * Columnas del catálogo.
 */
function mdc_loop_columns() {
	return 3;
}
add_filter( 'loop_shop_columns', 'mdc_loop_columns', 20 );

/**
 * Miniaturas relacionadas: 3 productos, no 4.
 *
 * En un catálogo corto, "también te puede interesar" con 4 huecos acaba
 * mostrando relleno. Con 3 solo salen los que de verdad encajan.
 */
function mdc_related_products_args( $args ) {
	$args['posts_per_page'] = 3;
	$args['columns']        = 3;
	return $args;
}
add_filter( 'woocommerce_output_related_products_args', 'mdc_related_products_args', 20 );

/**
 * Quita el mensaje de "categoría" duplicado bajo el título del catálogo.
 */
remove_action( 'woocommerce_archive_description', 'woocommerce_taxonomy_archive_description', 10 );
add_action( 'woocommerce_archive_description', 'woocommerce_taxonomy_archive_description', 5 );

/**
 * Sello de confianza bajo el botón de compra.
 *
 * Envío, plazo y garantía en el punto exacto de la duda. Es de las
 * intervenciones que más mueven la conversión en ticket alto.
 */
function mdc_trust_badges() {
	$items = array(
		__( 'Envío en 24–48 h en península', 'maestros-del-corte' ),
		__( 'Devolución gratuita en 30 días', 'maestros-del-corte' ),
		__( 'Garantía Cuperinox', 'maestros-del-corte' ),
	);

	echo '<ul class="mdc-trust">';
	foreach ( $items as $item ) {
		echo '<li>' . esc_html( $item ) . '</li>';
	}
	echo '</ul>';
}
add_action( 'woocommerce_after_add_to_cart_form', 'mdc_trust_badges', 15 );
