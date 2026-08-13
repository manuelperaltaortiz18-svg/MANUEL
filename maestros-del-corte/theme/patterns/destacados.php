<?php
/**
 * Title: Portada — productos destacados
 * Slug: maestros-del-corte/destacados
 * Categories: maestros-del-corte
 * Description: Rejilla de productos marcados como destacados en WooCommerce.
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"var:preset|spacing|60","bottom":"var:preset|spacing|60"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="padding-top:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--60)">

	<!-- wp:group {"align":"wide","style":{"spacing":{"margin":{"bottom":"var:preset|spacing|50"}}},"layout":{"type":"flex","justifyContent":"space-between","flexWrap":"wrap"}} -->
	<div class="wp-block-group alignwide" style="margin-bottom:var(--wp--preset--spacing--50)">
		<!-- wp:heading {"level":2} -->
		<h2 class="wp-block-heading">La selección</h2>
		<!-- /wp:heading -->

		<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.875rem"}}} -->
		<p style="font-size:0.875rem"><a href="/tienda/">Ver todo el catálogo →</a></p>
		<!-- /wp:paragraph -->
	</div>
	<!-- /wp:group -->

	<!-- wp:woocommerce/handpicked-products {"align":"wide","columns":3,"editMode":false,"products":[]} /-->

</div>
<!-- /wp:group -->
