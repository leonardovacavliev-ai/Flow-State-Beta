<!-- Dry run of scripts/import_catalog.py, 2026-10-14, live catalog and partner sites; the knowledge-base rows were a read-only copy of production (eval/seed_local_db.py). Nothing was written. -->

# Catalog import: dry run

## Summary

| | count |
|---|---:|
| catalog cards (detail pages) | 177 |
| integrations in the catalog | 154 |
| integrations to create (as `listed`) | 145 |
| existing integrations whose catalog fields change | 9 |
| proposals: Yotpo guides | 88 |
|   of which renamed guides | 6 |
| proposals: partner pages from the catalog | 135 |
| proposals: partner mechanics articles (new) | 213 |
| guides gone (404, no renamed match) | 1 |
| detail pages with nothing documentary | 13 |
| integrations with no help centre found | 37 |
| links already in the knowledge base (skipped) | 16 |
| links already proposed (skipped) | 0 |
| cards removed since the last import | 0 |
| name clashes | 0 |

## Integrations to create, by default type

**content** (23): Bazaarvoice (`bazaarvoice`), Beautytap (`beautytap`), Chimeable (`chimeable`), Cohley (`cohley`), ExpertVoice (`expertvoice`), Facebook (`facebook`), Google (`google`), Instagram (`instagram`), Judge.me (`judge_me`), Later (`later`), LoudCrowd (`loudcrowd`), PowerReviews (`powerreviews`), Refersion (`refersion`), Skeepers (previously Octoly) (`skeepers`), Social Nature (`social_nature`), SoPost (`sopost`), Stellar Reviews (`stellar_reviews`), Target (`target`), TikTok Shop (`tiktok_shop`), Trend (`trend`), Try & Review (`try_review`), Twitter (`twitter`), Wonderment (`wonderment`)

**data** (35): AddGlow (`addglow`), Adscale (`adscale`), AfterShip Tracking (`aftership`), Alloy (`alloy_automation`), Antavo (`antavo`), BHN Rewards (formerly Rybbon) (`bhn_rewards`), Daasity (`daasity`), DaitaFix (`daitafix`), DataGrail (`datagrail`), EcoCart (`ecocart`), Fueled (`fueled`), Glew (`glew`), GoGenerosity (`gogenerosity`), Harbor (`harbor`), LateShipment.com (`lateshipment_com`), Lexer (`lexer`), LoyaltyLion (`loyaltylion`), MESA (`mesa`), Order Desk (`order_desk`), Pie Eye (`pie_eye`), PostPilot (`postpilot`), ProductsUp (`productsup`), Rise.ai (`rise_ai`), Rush (`rush`), Shopify Flow (`shopify_flow`), ShoppingGives (`shoppinggives`), Smile.io (`smile_io`), Stitch (`stitch`), Syncly (`syncly`), Tray.io (`tray_io`), Treet (`treet`), Triple Whale (`triple_whale`), ViralSweep (`viralsweep`), Virtue (`virtue`), Zinrelo (`zinrelo`)

**messaging** (19): AdRoll (`adroll`), Braze (`braze`), Cordial (`cordial`), Dondy (`dondy`), Drip (`drip`), Flashchat (`flashchat`), Hubspot (`hubspot`), Insider (`insider`), Klaviyo Customer Hub (`klaviyo_customer_hub`), Mailchimp (`mailchimp`), Movable Ink (`movable_ink`), Optimizely (Zaius) (`optimizely`), Optimove (`optimove`), Remarkety (`remarkety`), Retention Science (`retention_science`), Rule (`rule`), Sailthru (`sailthru`), Salesforce Marketing Cloud (`salesforce_marketing_cloud`), Zembula (`zembula`)

**service** (7): Dixa (`dixa`), Gladly (`gladly`), Gorgias (`gorgias`), Re:amaze (`reamaze`), Rep AI (`rep_ai`), Siena (`siena`), Zendesk (`zendesk`)

**storefront** (61): Adobe Commerce (Magento) (`adobe_commerce_magento`), AfterShip Personalization (`aftership_personalization`), Akeneo (`akeneo`), Amasty (`amasty`), Ampifyme (`ampifyme`), Appbrew (`appbrew`), Beeketing Boost Sales (`beeketing_boost_sales`), BigCommerce (`bigcommerce`), BlueConic (`blueconic`), Bold Commerce (`bold_commerce`), Boost Commerce (`boostcommerce`), Builder.io (`builder_io`), Checkout Review (`checkout`), Checkout Plus (`checkout_plus`), Dialogue (`dialogue`), Digioh (`digioh`), Dotdigital (`dotdigital_personalization`), EComposer (`ecomposer`), Fast Simon (`fast_simon`), Findify (`findify`), Fobi (`fobi`), Fomo (`fomo`), Fuego (`fuego`), GemPages (`gempages`), Heartland Retail by Hyperspace (`heartland_retail_by_hyperspace`), Kimonix (`kimonix`), Klevu (`klevu`), KnoCommerce (`knocommerce`), LimeSpot (`limespot`), Loop Subscriptions (`loop_subscriptions`), MageNative (`magenative`), Nosto (`nosto`), Novel (`novel`), Ordergroove (`ordergroove`), PageFly (`pagefly`), Plobal Apps (`plobal_apps`), poq (`poq`), ProveSource (`provesource`), Reactiv (`reactiv`), Rebuy (`rebuy`), Recharge (`recharge`), Salesforce Commerce Cloud (`salesforce_commerce_cloud`), Searchanise (`searchanise`), Searchspring (`searchspring`), Shoelace (`shoelace`), Shogun (`shogun`), Shopeaks (`shopeaks`), Shopify (`shopify`), Shopify Plus (`shopify_plus`), Shopify POS (`shopify_point_of_sale`), Square POS by Defsys (`square_pos_by_defsys`), Subtotal (`subtotal`), Swapt (`swapt`), Talkable (`talkable`), Tapcart (`tapcart`), Teamwork Commerce (`teamwork_commerce`), Vajro (`vajro`), Volusion (`volusion`), Weglot (`weglot`), WooCommerce (`woocommerce`), Yieldify (`yieldify`)

## Type conflicts (18)

Categories of more than one type. The default is the first of messaging → service → storefront → content → data; an admin can change it.

| integration | default | categories point to |
|---|---|---|
| AdRoll | messaging | data, messaging |
| Akeneo | storefront | data, storefront |
| Dondy | messaging | data, messaging |
| Drip | messaging | data, messaging |
| Facebook | content | content, data |
| Google | content | content, data |
| Instagram | content | content, data |
| Kimonix | storefront | data, storefront |
| Klaviyo Customer Hub | messaging | messaging, storefront |
| Movable Ink | messaging | data, messaging |
| Optimizely (Zaius) | messaging | data, messaging |
| Optimove | messaging | data, messaging |
| Shopeaks | storefront | data, storefront |
| Subtotal | storefront | data, storefront |
| Talkable | storefront | data, storefront |
| Weglot | storefront | data, storefront |
| Wonderment | content | content, data |
| Zembula | messaging | data, messaging |

## Existing integrations whose catalog fields would change

- `attentive`: catalog_slugs: [] → ["attentive", "attentive-loyalty"]; categories: [] → ["email-marketing", "sms-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → Yotpo and Attentive’s integration, allows you to sync rev…
- `brevo_pushowl`: catalog_slugs: [] → ["brevo-pushowl", "brevo-pushowl-loyalty"]; categories: [] → ["email-marketing", "sms-marketing"]; products: [] → ["reviews", "loyalty"]; catalog_description: null → Yotpo and Brevo PushOwl’s integration syncs real time loy…
- `dotdigital`: catalog_slugs: [] → ["dotdigital", "dotdigital-loyalty"]; categories: [] → ["email-marketing", "sms-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → Yotpo & Dotdigital’s integration enables brands to craft …
- `emarsys`: catalog_slugs: [] → ["emarsys"]; categories: [] → ["email-marketing"]; products: [] → ["loyalty"]; catalog_description: null → With Yotpo’s integration with Emarsys, brands can design …
- `klaviyo`: catalog_slugs: [] → ["klaviyo-loyalty", "klaviyo"]; categories: [] → ["data-automation", "email-marketing", "sms-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → Yotpo and Klaviyo's integration, allows you to sync revie…
- `listrak`: catalog_slugs: [] → ["listrak-loyalty", "listrak"]; categories: [] → ["email-marketing", "sms-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → Yotpo's integration with Listrak pulls product ratings an…
- `ometria`: catalog_slugs: [] → ["ometria"]; categories: [] → ["data-automation", "email-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → The Yotpo & Ometria integration allows brands the ability…
- `omnisend`: catalog_slugs: [] → ["omnisend", "omnisend-loyalty"]; categories: [] → ["email-marketing"]; products: [] → ["loyalty", "reviews"]; catalog_description: null → Integrate Yotpo and Omnisend and leverage powerful review…
- `postscript`: catalog_slugs: [] → ["postscript"]; categories: [] → ["sms-marketing"]; products: [] → ["loyalty"]; catalog_description: null → Yotpo and Postscript's integration, allows you to sync lo…

## Proposals

Labels: Yotpo guides are pre-filled from their own header when it names one product (empty when it names both, or none). Partner pages are left empty. Mechanics articles are pre-filled `shared`: they explain the partner's features, not a Yotpo product. An admin confirms every label.

### Yotpo guides (88)

| integration | link | label | note |
|---|---|---|---|
| `adobe_commerce_magento` | https://support.yotpo.com/docs/adobe-commerce-2-setting-up-yotpo-reviews-extension-245-330 | — | Yotpo guide linked from the catalog |
| `adroll` | https://support.yotpo.com/docs/adroll-integration-guide | reviews | Yotpo guide linked from the catalog |
| `alloy_automation` | https://support.yotpo.com/docs/alloy-integration-guide | — | Yotpo guide linked from the catalog |
| `amasty` | https://support.yotpo.com/docs/amasty-integration-guide | reviews | Yotpo guide linked from the catalog |
| `ampifyme` | https://support.yotpo.com/docs/ampifyme-integration-guide | reviews | Yotpo guide linked from the catalog |
| `antavo` | https://support.yotpo.com/docs/antavo-integration-guide | reviews | Yotpo guide linked from the catalog |
| `beautytap` | https://support.yotpo.com/docs/beautytap-integration-guide | reviews | Yotpo guide linked from the catalog |
| `bhn_rewards` | https://support.yotpo.com/docs/rybbon-integration-guide-for-yotpo-loyalty-referrals | loyalty | redirected from https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-rybbon |
| `bigcommerce` | https://support.yotpo.com/docs/bigcommerce-stencil-installing-yotpo-reviews-on-stencil | reviews | Yotpo guide linked from the catalog |
| `bigcommerce` | https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-bigcommerce | loyalty | Yotpo guide linked from the catalog |
| `bold_commerce` | https://support.yotpo.com/docs/bold-commerce-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `braze` | https://support.yotpo.com/docs/braze-integration-guide | — | Yotpo guide linked from the catalog |
| `builder_io` | https://support.yotpo.com/docs/builderio-integration-guide | reviews | renamed from https://support.yotpo.com/docs/builder-integration-guide |
| `cohley` | https://support.yotpo.com/docs/cohley-integration-guide | reviews | Yotpo guide linked from the catalog |
| `cordial` | https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-cordial | loyalty | Yotpo guide linked from the catalog |
| `dotdigital` | https://support.yotpo.com/docs/dotdigital-integration-guide-for-yotpo-reviews | reviews | Yotpo guide linked from the catalog |
| `dotdigital_personalization` | https://support.yotpo.com/docs/fresh-relevance-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `drip` | https://support.yotpo.com/docs/drip-integration-guide | reviews | Yotpo guide linked from the catalog |
| `ecocart` | https://support.yotpo.com/docs/ecocart-integration-guide-for-loyalty-referrals-and-smsbump | loyalty | Yotpo guide linked from the catalog |
| `expertvoice` | https://support.yotpo.com/docs/expertvoice-integration-guide | reviews | Yotpo guide linked from the catalog |
| `facebook` | https://support.yotpo.com/docs/social-push | reviews | Yotpo guide linked from the catalog |
| `fast_simon` | https://support.yotpo.com/docs/fast-simon-integration-guide | reviews | Yotpo guide linked from the catalog |
| `findify` | https://support.yotpo.com/docs/findify-integration-guide | reviews | Yotpo guide linked from the catalog |
| `flashchat` | https://support.yotpo.com/docs/flashchat-integration-guide | reviews | Yotpo guide linked from the catalog |
| `fomo` | https://support.yotpo.com/docs/fomo-integration-guide | reviews | Yotpo guide linked from the catalog |
| `gempages` | https://support.yotpo.com/docs/gempages-integration-guide | reviews | Yotpo guide linked from the catalog |
| `glew` | https://support.yotpo.com/docs/glew-integration-guide | — | Yotpo guide linked from the catalog |
| `google` | https://support.yotpo.com/docs/google-seller-ratings | reviews | Yotpo guide linked from the catalog |
| `google` | https://support.yotpo.com/docs/google-shopping-syndication | reviews | Yotpo guide linked from the catalog |
| `gorgias` | https://support.yotpo.com/docs/gorgias-integration-guide-for-reviews-and-loyalty-referrals | — | Yotpo guide linked from the catalog |
| `heartland_retail_by_hyperspace` | https://support.yotpo.com/docs/heartland-retail-point-of-sale-integration-guide-for-loyalty | loyalty | renamed from https://support.yotpo.com/docs/heartland-retail-point-of-sale-integration-guide |
| `hubspot` | https://support.yotpo.com/docs/hubspot-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `hubspot` | https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-hubspot | loyalty | Yotpo guide linked from the catalog |
| `judge_me` | https://support.yotpo.com/docs/integrating-loyalty-referrals-and-judgeme | loyalty | Yotpo guide linked from the catalog |
| `klaviyo_customer_hub` | https://support.yotpo.com/docs/yotpo-loyalty-referrals-klaviyo-customer-hub | loyalty | Yotpo guide linked from the catalog |
| `klevu` | https://support.yotpo.com/docs/klevu-integration-guide | reviews | Yotpo guide linked from the catalog |
| `later` | https://support.yotpo.com/docs/mavrck-integration-guide | reviews | Yotpo guide linked from the catalog |
| `lexer` | https://support.yotpo.com/docs/lexer-integration-guide-for-loyalty-referrals | loyalty | Yotpo guide linked from the catalog |
| `lexer` | https://support.yotpo.com/docs/lexer-integration-guide-for-reviews | reviews | redirected from https://support.yotpo.com/docs/lexer-integration-guide-for-reviews-5782145 |
| `limespot` | https://support.yotpo.com/docs/limespot-integration-guide | reviews | Yotpo guide linked from the catalog |
| `listrak` | https://support.yotpo.com/docs/listrak-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `loudcrowd` | https://support.yotpo.com/docs/loudcrowd-integration-guide-for-loyalty-referrals | loyalty | renamed from https://support.yotpo.com/docs/loudcrowd-integration-guide |
| `mailchimp` | https://support.yotpo.com/docs/mailchimp-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `mailchimp` | https://support.yotpo.com/docs/mailchimp-integration-yotpo-loyalty-referrals | loyalty | Yotpo guide linked from the catalog |
| `movable_ink` | https://support.yotpo.com/docs/movable-ink-integration-guide | reviews | Yotpo guide linked from the catalog |
| `nosto` | https://support.yotpo.com/docs/nosto-integratio-guide-reviews-ugc | reviews | Yotpo guide linked from the catalog |
| `novel` | https://support.yotpo.com/docs/yotpo-loyalty-referrals-novel-integration | loyalty | Yotpo guide linked from the catalog |
| `omnisend` | https://support.yotpo.com/docs/omnisend-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `optimove` | https://support.yotpo.com/docs/optimove-integration-guide-for-yotpo-loyalty-referrals | loyalty | renamed from https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-optimove |
| `order_desk` | https://support.yotpo.com/docs/order-desk-integration-guide-for-reviews | reviews | redirected from https://support.yotpo.com/docs/order-desk-integration-guide |
| `ordergroove` | https://support.yotpo.com/docs/ordergroove-integration-guide-for-yotpo-loyalty-referrals | loyalty | redirected from https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-ordergroove |
| `pagefly` | https://support.yotpo.com/docs/pagefly-integration-guide-for-reviews | reviews | renamed from https://support.yotpo.com/docs/pagefly-integration-guide |
| `pie_eye` | https://support.yotpo.com/docs/pieeye-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `plobal_apps` | https://support.yotpo.com/docs/plobal-apps-integration-guide | — | Yotpo guide linked from the catalog |
| `poq` | https://support.yotpo.com/docs/poq-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |
| `productsup` | https://support.yotpo.com/docs/productsup-integration-guide | reviews | Yotpo guide linked from the catalog |
| `reamaze` | https://support.yotpo.com/docs/reamaze-integration-guide-for-reviews-and-loyalty-referrals | — | redirected from https://support.yotpo.com/docs/reamaze-integration-guide |
| `rebuy` | https://support.yotpo.com/docs/rebuy-integration-guide-for-yotpo-loyalty-referrals | loyalty | Yotpo guide linked from the catalog |
| `recharge` | https://support.yotpo.com/docs/recharge-integration-guide-for-yotpo-loyalty-referrals | loyalty | Yotpo guide linked from the catalog |
| `refersion` | https://support.yotpo.com/docs/refersion-integration-guide-for-yotpo-loyalty-referrals | loyalty | Yotpo guide linked from the catalog |
| `remarkety` | https://support.yotpo.com/docs/remarkety-integration-guide-for-reviews | reviews | redirected from https://support.yotpo.com/docs/remarkety-integration-guide |
| `retention_science` | https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-retention-science | loyalty | Yotpo guide linked from the catalog |
| `sailthru` | https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-sailthru | loyalty | Yotpo guide linked from the catalog |
| `salesforce_commerce_cloud` | https://support.yotpo.com/docs/salesforce-commerce-cloud-installing-yotpo-reviews | reviews | Yotpo guide linked from the catalog |
| `salesforce_marketing_cloud` | https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-salesforce-marketing-cloud | loyalty | Yotpo guide linked from the catalog |
| `searchanise` | https://support.yotpo.com/docs/searchanise-integration-guide | reviews | Yotpo guide linked from the catalog |
| `searchspring` | https://support.yotpo.com/docs/searchspring-integration-guide | reviews | Yotpo guide linked from the catalog |
| `shoelace` | https://support.yotpo.com/docs/shoelace-integration-guide | reviews | Yotpo guide linked from the catalog |
| `shogun` | https://support.yotpo.com/docs/shogun-integration-guide | reviews | Yotpo guide linked from the catalog |
| `shopify` | https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20 | loyalty | Yotpo guide linked from the catalog |
| `shopify_flow` | https://support.yotpo.com/docs/creating-yotpo-workflows-in-shopify-flow | reviews | Yotpo guide linked from the catalog |
| `shopify_plus` | https://support.yotpo.com/docs/shopify-installing-yotpo-reviews-on-online-store-20 | reviews | Yotpo guide linked from the catalog |
| `shopify_point_of_sale` | https://support.yotpo.com/docs/integrating-loyalty-and-referrals-with-shopify-point-of-sale-pos | loyalty | Yotpo guide linked from the catalog |
| `shopify_point_of_sale` | https://support.yotpo.com/docs/shopify-point-of-sale-pos-integration-for-reviews | reviews | Yotpo guide linked from the catalog |
| `shoppinggives` | https://support.yotpo.com/docs/integrating-donations-with-loyalty-referrals-shoppinggives | loyalty | Yotpo guide linked from the catalog |
| `skeepers` | https://support.yotpo.com/docs/octoly-integration-guide | reviews | Yotpo guide linked from the catalog |
| `social_nature` | https://support.yotpo.com/docs/social-nature-integration-guide | reviews | Yotpo guide linked from the catalog |
| `sopost` | https://support.yotpo.com/docs/sopost-integration-guide | reviews | Yotpo guide linked from the catalog |
| `tapcart` | https://support.yotpo.com/docs/tapcart-yotpo-integration-guide | — | Yotpo guide linked from the catalog |
| `tiktok_shop` | https://support.yotpo.com/docs/tiktok-shop-yotpo-reviews-integration | reviews | Yotpo guide linked from the catalog |
| `trend` | https://support.yotpo.com/docs/trend-integration-guide | reviews | Yotpo guide linked from the catalog |
| `vajro` | https://support.yotpo.com/docs/vajro-integration-guide | reviews | Yotpo guide linked from the catalog |
| `viralsweep` | https://support.yotpo.com/docs/viralsweep-integration-guide | reviews | Yotpo guide linked from the catalog |
| `volusion` | https://support.yotpo.com/docs/volusion-installing-yotpo | reviews | Yotpo guide linked from the catalog |
| `weglot` | https://support.yotpo.com/docs/weglot-integration-guide | — | Yotpo guide linked from the catalog |
| `woocommerce` | https://support.yotpo.com/docs/woocommerce-installing-yotpo | reviews | Yotpo guide linked from the catalog |
| `zembula` | https://support.yotpo.com/docs/zembula-integration-guide-for-reviews | reviews | renamed from https://support.yotpo.com/docs/zembula-integration-guide |
| `zendesk` | https://support.yotpo.com/docs/zendesk-integration-guide-for-reviews | reviews | Yotpo guide linked from the catalog |

### Partner pages from the catalog (135)

| integration | link | label | note |
|---|---|---|---|
| `addglow` | https://www.addglow.com/yotpo-integration | — | partner page linked from the catalog |
| `adobe_commerce_magento` | https://commercemarketplace.adobe.com/yotpo-module-yotpo.html | — | partner page linked from the catalog |
| `adobe_commerce_magento` | https://marketplace.magento.com/yotpo-magento2-module-yotpo-loyalty.html | — | partner page linked from the catalog |
| `adscale` | https://help.adscale.com/en/articles/8385340-using-yotpo-in-your-ad-strategies | — | partner page linked from the catalog |
| `adscale` | https://help.adscale.com/en/articles/8385656-integrating-yotpo-with-adscale | — | partner page linked from the catalog |
| `aftership` | https://www.aftership.com/integrations/yotpo | — | partner page linked from the catalog |
| `aftership_personalization` | https://support-personalization.automizely.com/en/article/set-up-yotpo-integration-1p1o97i | — | partner page linked from the catalog |
| `aftership_personalization` | https://www.aftership.com/integrations/yotpo/personalization?as_source=www.aftership.com%2Fintegrations%2Fyotpo | — | partner page linked from the catalog |
| `akeneo` | https://help.akeneo.com/rating-reviews/rating-reviews-with-yotpo | — | partner page linked from the catalog |
| `alloy_automation` | https://runalloy.com/integrations/yotpo | — | partner page linked from the catalog |
| `attentive` | https://help.attentivemobile.com/hc/en-us/articles/41245602462740-Yotpo-Reviews | — | partner page linked from the catalog |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/4406522748180 | — | partner page linked from the catalog |
| `bhn_rewards` | https://www.rybbon.net/yotpo-integration | — | partner page linked from the catalog |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/246955-yotpo-integration | — | partner page linked from the catalog |
| `bold_commerce` | https://blog.boldcommerce.com/yotpo-integration | — | partner page linked from the catalog |
| `boostcommerce` | https://help.boostcommerce.net/article/392-yotpo | — | partner page linked from the catalog |
| `braze` | https://www.braze.com/docs/partners/message_orchestration/channel_extensions/ecommerce/yotpo | — | partner page linked from the catalog |
| `builder_io` | https://www.builder.io/c/docs/yotpo-app-template | — | partner page linked from the catalog |
| `checkout` | https://checkoutreview.com/2026/07/29/how-to-add-yotpo-reviews-to-the-shopify-checkout-with-checkout-review | — | partner page linked from the catalog |
| `checkout_plus` | https://www.tryplusapps.com/blog/how-to-add-yotpo-reviews-to-the-shopify-checkout-with-checkout-plus | — | partner page linked from the catalog |
| `chimeable` | https://www.chimeable.com/blog/yotpo | — | partner page linked from the catalog |
| `daasity` | https://support.daasity.com/knowledge/yotpo-dashboard | — | partner page linked from the catalog |
| `daasity` | https://support.daasity.com/knowledge/yotpo-setup | — | partner page linked from the catalog |
| `daitafix` | https://daitafix.com/yotpo/setup | — | partner page linked from the catalog |
| `dialogue` | https://help.nowdialogue.com/en/articles/9569370-yotpo-loyalty-dialogue-integration | — | partner page linked from the catalog |
| `dialogue` | https://help.nowdialogue.com/en/articles/9929012-yotpo-visual-ugc-dialogue-integration | — | partner page linked from the catalog |
| `dialogue` | https://help.nowdialogue.com/en/articles/9929014-yotpo-reviews-dialogue-integration | — | partner page linked from the catalog |
| `digioh` | https://get.digioh.com/yotpo | — | partner page linked from the catalog |
| `digioh` | https://help.digioh.com/knowledgebase/digioh-yotpo-integration | — | partner page linked from the catalog |
| `dixa` | https://support.dixa.help/en/articles/1879-yotpo-integration | — | partner page linked from the catalog |
| `dondy` | https://www.dondy.net/post/how-to-send-whatsapp-review-requests-using-yotpo-with-dondy | — | partner page linked from the catalog |
| `dondy` | https://www.dondy.net/post/how-to-send-whatsapp-thank-you-messages-after-yotpo-reviews-using-dondy-shopify-flow | — | partner page linked from the catalog |
| `dotdigital` | https://support.dotdigital.com/en/articles/12674501-integrate-yotpo-loyalty-with-dotdigital | — | partner page linked from the catalog |
| `dotdigital` | https://support.dotdigital.com/en/articles/8199358-add-yotpo-reviews-to-campaigns-pages-and-forms | — | partner page linked from the catalog |
| `dotdigital` | https://support.dotdigital.com/en/articles/8199787-integrate-yotpo-reviews-with-dotdigital | — | partner page linked from the catalog |
| `dotdigital` | https://support.dotdigital.com/en/articles/8199790-use-yotpo-review-data-in-dotdigital | — | partner page linked from the catalog |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8523333-import-review-data | — | partner page linked from the catalog |
| `drip` | https://www.drip.com/integrations/yotpo | — | partner page linked from the catalog |
| `drip` | https://www.drip.com/learn/docs/guides/yotpo-integration-instructions | — | partner page linked from the catalog |
| `ecomposer` | https://help.ecomposer.io/docs/extensions-integrations/third-party-extensions/yotpo-reviews | — | partner page linked from the catalog |
| `findify` | https://developers.findify.io/docs/third-party-yotpo | — | partner page linked from the catalog |
| `fuego` | https://wiki.fuego.io/articles/3831972798-fuego-x-yotpo-loyalty-integration | — | partner page linked from the catalog |
| `fuego` | https://wiki.fuego.io/articles/8581677172-fuego-x-yotpo-reviews-integration | — | partner page linked from the catalog |
| `fuego` | https://wiki.fuego.io/articles/9007335298-fuego-x-yotpo-visual-ugc-integration | — | partner page linked from the catalog |
| `gempages` | https://help.gempages.net/articles/add-yotpo-product-reviews | — | partner page linked from the catalog |
| `gladly` | https://help.gladly.com/docs/yotpo-on-app-platform | — | partner page linked from the catalog |
| `glew` | https://www.glew.io/articles/4-ecommerce-apps-you-need | — | partner page linked from the catalog |
| `glew` | https://www.glew.io/integrations/yotpo | — | partner page linked from the catalog |
| `gogenerosity` | https://help.gogenerosity.com/how-to-donate-yotpo-loyalty-points | — | partner page linked from the catalog |
| `gorgias` | https://www.gorgias.com/blog/yotpo-integration | — | partner page linked from the catalog |
| `harbor` | https://www.harborloyalty.com/yotpo | — | partner page linked from the catalog |
| `harbor` | https://www.harborloyalty.com/yotpo-setup | — | partner page linked from the catalog |
| `heartland_retail_by_hyperspace` | https://hyperspacehq.com/yotpo-connector-heartland-retail | — | partner page linked from the catalog |
| `insider` | https://academy.useinsider.com/docs/external-platform-integrations-yotpo | — | partner page linked from the catalog |
| `insider` | https://academy.useinsider.com/docs/sending-yotpo-data-to-insider | — | partner page linked from the catalog |
| `judge_me` | https://support.judge.me/support/home | — | partner page linked from the catalog |
| `kimonix` | http://help.kimonix.com/article/activating-yotpo-product-reviews-integration | — | partner page linked from the catalog |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us/articles/46364536713755 | — | partner page linked from the catalog |
| `klevu` | https://help.klevu.com/support/solutions/articles/5000873503-integrating-yotpo-with-klevu | — | partner page linked from the catalog |
| `knocommerce` | https://docs.knocommerce.com/en/articles/9722856-yotpo-integration | — | partner page linked from the catalog |
| `lateshipment_com` | http://www.lateshipment.com/yotpo | — | partner page linked from the catalog |
| `lexer` | https://learn.lexer.io/docs/yotpo | — | partner page linked from the catalog |
| `limespot` | https://support.limespot.com/en/articles/3968735-integrating-limespot-with-yotpo-reviews | — | partner page linked from the catalog |
| `limespot` | https://support.limespot.com/en/articles/9966828-integrating-limespot-with-yotpo-loyalty-referrals | — | partner page linked from the catalog |
| `listrak` | https://help.listrak.com/en/articles/2239379-integration-guide-ratings-and-reviews | — | partner page linked from the catalog |
| `loop_subscriptions` | https://learn.loopwork.co/en/article/yotpo-loyalty-a7wgjr | — | partner page linked from the catalog |
| `loudcrowd` | https://help.loudcrowd.com/en/articles/6088177-how-to-integrate-with-yotpo | — | partner page linked from the catalog |
| `magenative` | https://magenative.com/integrations/yotpo | — | partner page linked from the catalog |
| `mailchimp` | https://mailchimp.com/help/connect-disconnect-yotpo | — | partner page linked from the catalog |
| `mailchimp` | https://mailchimp.com/help/connect-disconnect-yotpo-loyalty-referrals | — | partner page linked from the catalog |
| `mesa` | https://docs.getmesa.com/article/1238-yotpo-loyalty | — | partner page linked from the catalog |
| `mesa` | https://docs.getmesa.com/connect/yotpo | — | partner page linked from the catalog |
| `mesa` | https://docs.getmesa.com/connect/yotpo-loyalty | — | partner page linked from the catalog |
| `mesa` | https://www.getmesa.com/connect/yotpo | — | partner page linked from the catalog |
| `movable_ink` | https://exchange.movableink.com/solution/yotpo | — | partner page linked from the catalog |
| `nosto` | https://partners.nosto.com/technologies/yotpo | — | partner page linked from the catalog |
| `novel` | https://support.novel.com/integrations/loyalty/yotpo-1 | — | partner page linked from the catalog |
| `ometria` | https://ometria.partnerpage.io/tech-partners/yotpo | — | partner page linked from the catalog |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/4801234544029-Setting-up-Yotpo-product-reviews | — | partner page linked from the catalog |
| `omnisend` | https://support.omnisend.com/en/articles/2851596-integration-with-yotpo-product-reviews | — | partner page linked from the catalog |
| `omnisend` | https://support.omnisend.com/en/articles/5967363-integration-with-yotpo-loyalt | — | partner page linked from the catalog |
| `optimizely` | https://apps.zaius.com/yotpo-swel | — | partner page linked from the catalog |
| `optimove` | https://academy.optimove.com/en/article/yotpo-loyalty | — | partner page linked from the catalog |
| `order_desk` | https://help.orderdesk.com/article/690-yotpo-integration | — | partner page linked from the catalog |
| `order_desk` | https://www.orderdesk.com/integrations/yotpo | — | partner page linked from the catalog |
| `pagefly` | https://help.pagefly.io/support-policy | — | partner page linked from the catalog |
| `pie_eye` | https://pii.ai/integrations/yotpo-integration | — | partner page linked from the catalog |
| `postpilot` | https://help.postpilot.com/knowledge/integrating-with-yotpo | — | partner page linked from the catalog |
| `powerreviews` | https://www.powerreviews.com/yotpo-brand-syndication | — | partner page linked from the catalog |
| `provesource` | https://help.provesrc.com/en/articles/3605959-add-yotpo-reviews-to-your-website | — | partner page linked from the catalog |
| `provesource` | https://provesrc.com/blog/provesource-yotpo-the-best-way-to-build-trust-with-your-visitors | — | partner page linked from the catalog |
| `reactiv` | https://support.reactivapp.com/en/articles/9771616-setting-up-a-yotpo-reviews-integration | — | partner page linked from the catalog |
| `reactiv` | https://support.reactivapp.com/en/articles/9772405-setting-up-a-yotpo-loyalty-integration | — | partner page linked from the catalog |
| `reamaze` | https://www.reamaze.com/integrations/yotpo | — | partner page linked from the catalog |
| `rebuy` | https://help.rebuyengine.com/en/articles/6399623-adding-yotpo-product-reviews-to-rebuy-widgets | — | partner page linked from the catalog |
| `rebuy` | https://help.rebuyengine.com/en/articles/8648790-yotpo-loyalty-smart-cart-app | — | partner page linked from the catalog |
| `refersion` | https://support.refersion.com/en/articles/4393854-yotpo-loyalty-referrals-integration | — | partner page linked from the catalog |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/360000455966-Integrate-Yotpo-and-Remarkety | — | partner page linked from the catalog |
| `remarkety` | https://www.remarkety.com/blog/yotpo-reviews | — | partner page linked from the catalog |
| `rep_ai` | https://help.hellorep.ai/hc/en-us/articles/11487699568018-Yotpo-Reviews-integration | — | partner page linked from the catalog |
| `rep_ai` | https://help.hellorep.ai/hc/en-us/articles/30599156879634-yotpo-loyalty | — | partner page linked from the catalog |
| `rise_ai` | https://help.rise.ai/en/articles/4002591-rise-yotpo-integration | — | partner page linked from the catalog |
| `rise_ai` | https://rise.ai/blog/integrations/rise-with-yotpo-reviw-app | — | partner page linked from the catalog |
| `rule` | https://en.docs.rule.se/article/449-integrera-yotpo-loyalty-rewards-med-rule | — | partner page linked from the catalog |
| `rush` | https://support.rush.app/yotpoo-reviews-integration | — | partner page linked from the catalog |
| `salesforce_commerce_cloud` | https://www.salesforce.com/products/commerce-cloud/partner-marketplace/partners/yotpo-quick-launch-solution | — | partner page linked from the catalog |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/201185109-Yotpo-Integration | — | partner page linked from the catalog |
| `shogun` | https://getshogun.com/help/en/articles/2689995-how-do-i-display-reviews-on-my-shopify-pages | — | partner page linked from the catalog |
| `shogun` | https://getshogun.com/help/en/articles/3977880-yotpo-product-reviews-for-bigcommerce | — | partner page linked from the catalog |
| `shopeaks` | https://www.shopeaks.com/blog/how-to-connect-yotpo-reviews-to-your-shopeaks | — | partner page linked from the catalog |
| `shopify_plus` | https://www.shopify.com/partners/blog/beyond-the-build-yotpo | — | partner page linked from the catalog |
| `siena` | https://support.siena.cx/hc/en-us/articles/38988766545819-Siena-AI-Yotpo-Integration | — | partner page linked from the catalog |
| `smile_io` | https://blog.smile.io/smile-app-yotpo | — | partner page linked from the catalog |
| `smile_io` | https://help.smile.io/en/articles/4036202-yotpo-and-smile | — | partner page linked from the catalog |
| `stellar_reviews` | https://stellarreviews.com/yotpo | — | partner page linked from the catalog |
| `stitch` | https://www.stitchdata.com/docs/integrations/saas/yotpo | — | partner page linked from the catalog |
| `stitch` | https://www.stitchdata.com/integrations/yotpo | — | partner page linked from the catalog |
| `stitch` | https://www.stitchdata.com/integrations/yotpo/mode | — | partner page linked from the catalog |
| `subtotal` | https://subtotal.com/docs/integrations/yotpo | — | partner page linked from the catalog |
| `swapt` | https://swaptqr.com/integrations-yotpo | — | partner page linked from the catalog |
| `talkable` | https://docs.talkable.com/email_marketing_and_automation/yotpo | — | partner page linked from the catalog |
| `tapcart` | https://help.tapcart.com/en/articles/11120450-yotpo-reviews-tapcart | — | partner page linked from the catalog |
| `tapcart` | https://help.tapcart.com/en/articles/12261042-yotpo-loyalty-integration | — | partner page linked from the catalog |
| `teamwork_commerce` | https://www.teamworkcommerce.com/wp-content/uploads/2026/09/yotpo-merchant-guide.pdf | — | partner page linked from the catalog |
| `tray_io` | https://tray.io/connectors/yotpo-integrations | — | partner page linked from the catalog |
| `tray_io` | https://tray.io/documentation/connectors/service/yotpo?docs_source=search&docs_term=yotpo | — | partner page linked from the catalog |
| `treet` | https://treetbrandsuccess.zendesk.com/hc/en-us/articles/22226883026711-Issuing-Seller-Credit-Via-Your-Yotpo-Loyalty-Program | — | partner page linked from the catalog |
| `triple_whale` | https://kb.triplewhale.com/en/articles/9926955-yotpo-reviews-integration | — | partner page linked from the catalog |
| `viralsweep` | https://support.viralsweep.com/article/56-yotpo | — | partner page linked from the catalog |
| `viralsweep` | https://www.viralsweep.com/blog/increase-product-reviews-with-yotpo-and-viralsweep | — | partner page linked from the catalog |
| `viralsweep` | https://www.viralsweep.com/integrations/yotpo | — | partner page linked from the catalog |
| `virtue` | https://help.virtueimpact.com/en/articles/11583309-virtue-x-yotpo-rewards | — | partner page linked from the catalog |
| `virtue` | https://www.virtueimpact.com/post/virtue-x-yotpo-turn-loyalty-points-into-lasting-impact | — | partner page linked from the catalog |
| `wonderment` | https://docs.wonderment.com/article/6604v1nyzh-yotpo-integration-for-delivery-timing | — | partner page linked from the catalog |
| `woocommerce` | https://woocommerce.com/products/yotpo-social-reviews | — | partner page linked from the catalog |

### Partner mechanics articles (213)

| integration | link | label | note |
|---|---|---|---|
| `aftership` | https://support.aftership.com/en/returns | shared | "AfterShip Returns": returns, exchanges and store credit |
| `aftership` | https://support.aftership.com/en/tracking | shared | "AfterShip Tracking": tracking and notifications (the Yotpo guide or partner pages mention it) |
| `aftership` | https://support.aftership.com/en/tracking/articles/15441801-connect-shopify-with-aftership-tracking | shared | "Connect Shopify With AfterShip Tracking": tracking and notifications (the Yotpo guide or partner pages mention it) |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322506-how-to-add-trust-badges-to-the-checkout-page | shared | "How to Add Trust Badges to the Checkout Page Add trust badges to checkout in AfterShip Personalization: configure badge display, build customer trust,": results, badges and merchandising (the Yotpo guide or partner pages mention it) |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322510-display-product-recommendations-on-thank-you-page | shared | "Display Product Recommendations on Thank You Page Customize and add a cross-sell widget on the Thank You page in Shopify to boost sales with AfterShip": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322515-how-to-embed-smart-upsell-widgets-in-your-shopify-store-theme-1-0 | shared | "How to Embed Smart Upsell Widgets in Your Shopify Store Theme 1.0 Embed Smart Upsell Widgets in Your Shopify Store Theme 1.0 in AfterShip Personalizat": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `akeneo` | https://help.akeneo.com/en_US/serenity-manage-your-reference-entities/20-serenity-import-and-export-your-reference-entity-records | shared | "Serenity import and export your reference entity records": data sync and connectors |
| `akeneo` | https://help.akeneo.com/en_US/serenity-permissions/serenity-manage-the-interface-and-actions-accesses | shared | "Serenity manage the interface and actions accesses": workflows: triggers and actions |
| `akeneo` | https://help.akeneo.com/en_US/serenity-your-first-steps-with-akeneo/1-serenity-discover-the-dashboard-in-details | shared | "Serenity discover the dashboard in details": dashboards and reports |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/logistics-warehouse-automation | shared | "Logistics warehouse automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/shipping-fulfillment-automation | shared | "Shipping fulfillment automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/what-is-operations-automation | shared | "What is operations automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `ampifyme` | https://help.ampifyme.com/article/22-how-to-customize-the-language-section | shared | "How to customize the language section": blocks and components |
| `ampifyme` | https://help.ampifyme.com/article/79-how-do-i-get-people-to-subscribe-to-push-notifications-how-do-i-configure-the-prompt | shared | "How do I get people to subscribe to push notifications? How do I configure the prompt?": push notifications |
| `ampifyme` | https://help.ampifyme.com/article/88-how-to-configure-push-notifications-and-run-campaigns | shared | "How to Configure Push Notifications and Run Campaigns on Your Store": push notifications |
| `attentive` | https://help.attentive.com/hc/en-us/articles/360052420472-Create-Shopify-segments | shared | "Create Shopify segments": segments and lists (the Yotpo guide or partner pages mention it) |
| `attentive` | https://help.attentive.com/hc/en-us/articles/360056415972-Add-steps-to-a-journey | shared | "Add steps to a journey": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `attentive` | https://help.attentive.com/hc/en-us/articles/6355344582804-Create-a-segment-from-a-custom-attribute | shared | "Create a segment from a custom attribute": custom properties and events (the Yotpo guide or partner pages mention it) |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics/content-collection-partner | shared | "Partner Program": content, rights and galleries (the Yotpo guide or partner pages mention it) |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/ratings-reviews/content-display-style-guide | shared | "Content display style guide": content, rights and galleries (the Yotpo guide or partner pages mention it) |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/ratings-reviews/syndication | shared | "Syndication": product catalog and feeds |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/360016516051-How-can-I-check-Target-gift-cards-balance-inquiry | shared | "How can I check Target gift cards balance inquiry?": gift cards and store credit (the Yotpo guide or partner pages mention it) |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/360017431912-Can-I-request-incentive-plastic-cards-instead-of-E-Gift-from-BHN-Rewards | shared | "Can I request incentive plastic cards instead of E-Gift from BHN Rewards?": rewards and incentives (the Yotpo guide or partner pages mention it) |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/360061371492-How-to-use-your-prepaid-reward-card | shared | "How to use your prepaid reward card": rewards and incentives (the Yotpo guide or partner pages mention it) |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15847457-create-a-discount-with-bold-discounts | shared | "Create a Discount with Bold Discounts": discount codes |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15847482-does-bold-discounts-create-discount-codes | shared | "Does Bold Discounts Create Discount Codes?": discount codes |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15847510-how-are-discounts-applied-when-a-product-is-in-multiple-discount-groups | shared | "How are discounts applied when a product is in multiple discount groups?": discount codes |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9355408-set-up-boost-ai-search-discovery | shared | "Set up Boost AI Search & Discovery": results, badges and merchandising (the Yotpo guide or partner pages mention it) |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9355713-create-effective-filter-trees-best-practices | shared | "Create effective filter trees \(best practices\)": filters and facets |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9400263-basic-flow-to-set-up-a-boost-recommendation-widget | shared | "Basic flow to set up a Boost Recommendation widget": recommendation widgets |
| `braze` | https://www.braze.com/docs/user_guide/brazeai/decisioning_studio_go/composing_with_canvas | shared | "Composing with Canvas": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `braze` | https://www.braze.com/docs/user_guide/channels/whatsapp/use_cases/opt_in_flows | shared | "Opt-in flows": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/11477693-how-to-create-sms-automations-for-order-updates-with-shopify-flow-pushowl | shared | "How to Create SMS Automations for order updates with Shopify Flow & PushOwl You can now build fully automated SMS workflows using Shopify’s Flow app t": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/11561839-how-to-create-sms-automations-for-abandoned-checkout-with-shopify-flow-pushowl | shared | "How to Create SMS Automations for abandoned checkout with Shopify Flow & PushOwl You can now build fully automated SMS workflows using Shopify’s Flow ": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/4113148-segmentation-builder | shared | "Segmentation Builder Learn how to build an audience segment and the different conditions available to help you create highly specific segments.": segments and lists (the Yotpo guide or partner pages mention it) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/115005528508-Events | shared | "Events": custom properties and events (the Yotpo guide or partner pages mention it) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/360006891372-Create-an-internal-suppression-list | shared | "Create an internal suppression list": segments and lists (the Yotpo guide or partner pages mention it) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/360024573532-Create-a-pop-up-triggered-by-a-click-on-the-navigation-menu-in-mobile-and-desktop-devices | shared | "Create a pop-up triggered by a click on the navigation menu in mobile and desktop devices": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `daasity` | https://help.daasity.com/core-concepts/dashboards | shared | "Dashboards": dashboards and reports (the Yotpo guide or partner pages mention it) |
| `daasity` | https://help.daasity.com/getting-started/quickstart-guides/homepage-kpi-dashboard | shared | "Learn about Home Dashboard →": dashboards and reports (the Yotpo guide or partner pages mention it) |
| `daasity` | https://help.daasity.com/technical-docs/workflows-and-scheduling | shared | "Workflows & Scheduling": workflows: triggers and actions |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/getting-started | shared | "Request Manager": data subject requests (the Yotpo guide or partner pages mention it) |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/access-categories | shared | "Access Categories Request Lifecycle": data subject requests (the Yotpo guide or partner pages mention it) |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/deletion | shared | "Deletion Request Lifecycle": data subject requests (the Yotpo guide or partner pages mention it) |
| `dixa` | https://support.dixa.help/en/articles/1895-auto-adding-conversation-contacts-attributes-through-automations | shared | "Auto adding conversation contacts attributes through automations": rules and automations |
| `dixa` | https://support.dixa.help/en/articles/2001-how-to-create-and-use-macros | shared | "How to create and use macros": macros and replies |
| `dixa` | https://support.dixa.help/en/articles/2148-configurable-conversation-sidebar | shared | "Configurable conversation sidebar": customer profile in the sidebar |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/create-pause-clone-or-delete-an-automation/8rDHseRyg4rfX9KinRBs2L | shared | "Create, pause, clone, or delete an automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/create-your-first-whatsapp-automation/8rDHseRyg48xDwNqX73RF8 | shared | "Create your first WhatsApp automation": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/what-automations-can-you-build-with-dondy/8rDHseRyg1Pidpt8gA3kDo | shared | "What automations can you build with Dondy?": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198958-add-contacts-to-lists-and-programs | shared | "Add contacts to lists and programs": segments and lists (the Yotpo guide or partner pages mention it) |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8199074-use-personalisation-in-a-transactional-email | shared | "Use personalisation in a transactional email": personalisation in messages (the Yotpo guide or partner pages mention it) |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8523249-control-triggers-using-javascript | shared | "Control triggers using JavaScript": targeting and display rules |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8561045-test-trigger-programs | shared | "Test Trigger Programs": targeting and display rules |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/9123274-data-for-use-in-trigger-scripts | shared | "Data for use in trigger scripts": targeting and display rules |
| `ecomposer` | https://help.ecomposer.io/docs/ai-features/ai-product-page-generator | shared | "AI Product Page Generator": product pages |
| `ecomposer` | https://help.ecomposer.io/docs/ecomposer-editor/section | shared | "Section Overview": blocks and components (the Yotpo guide or partner pages mention it) |
| `ecomposer` | https://help.ecomposer.io/docs/theme-sections/section-builder | shared | "Theme Sections": blocks and components (the Yotpo guide or partner pages mention it) |
| `gempages` | https://help.gempages.net/articles/add-blog-review-section-to-blog-post-page | shared | "Add blog review section to blog post page": blocks and components (the Yotpo guide or partner pages mention it) |
| `gempages` | https://help.gempages.net/articles/add-firepush-sms-email-web-push | shared | "Add firepush sms email web push": push notifications |
| `gempages` | https://help.gempages.net/articles/update-all-product-pages-using-product-page-template | shared | "Update all product pages using product page template": product pages |
| `gladly` | https://help.gladly.com/docs/author-actions | shared | "Add an Action to Guide Sections": AI agent knowledge and actions |
| `gladly` | https://help.gladly.com/docs/customer-profile-and-my-customers-list-interface-overview | shared | "Customer Profile and My Customers List Interface Overview": customer profile in the sidebar |
| `gladly` | https://help.gladly.com/docs/workflows-and-guides | shared | "Workflow Triggers": rules and automations |
| `glew` | https://www.glew.io/articles/3-easy-steps-to-get-started-with-predictive-marketing | shared | "Easy steps to get started with predictive marketing": workflows: triggers and actions |
| `glew` | https://www.glew.io/articles/creating-an-annual-report-how-to-use-ecommerce-data-to-gain-insights-for-next-year | shared | "Creating an annual report how to use ecommerce data to gain insights for next year": dashboards and reports (the Yotpo guide or partner pages mention it) |
| `glew` | https://www.glew.io/articles/introducing-customer-export-and-advanced-filters-in-glew | shared | "Introducing customer export and advanced filters in glew": data sync and connectors (the Yotpo guide or partner pages mention it) |
| `gorgias` | https://docs.gorgias.com/en-US/articles/automations-279714 | shared | "Automation features (Flows & Order Management)": rules and automations (the Yotpo guide or partner pages mention it) |
| `gorgias` | https://docs.gorgias.com/en-US/articles/getting-started-with-ai-agent-294725 | shared | "Getting Started with AI Agent": AI agent knowledge and actions (the Yotpo guide or partner pages mention it) |
| `gorgias` | https://docs.gorgias.com/en-US/create-guidance-for-ai-agent-1362592 | shared | "Create guidance to give AI Agent knowledge about your business": AI agent knowledge and actions (the Yotpo guide or partner pages mention it) |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/360005491253-How-do-sales-sync-for-guest-customers | shared | "How do sales sync for guest customers?": customers at the point of sale |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/4412386320155-How-do-I-disable-E-Invoices-from-sending-automatically-to-my-customer-s-email-address | shared | "How do I disable E-Invoices from sending automatically to my customer's email address?": customers at the point of sale |
| `hubspot` | https://knowledge.hubspot.com/automation | shared | "Automation": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `hubspot` | https://knowledge.hubspot.com/properties/hubspots-default-contact-properties | shared | "HubSpot's default contact properties": custom properties and events (the Yotpo guide or partner pages mention it) |
| `hubspot` | https://knowledge.hubspot.com/workflows/choose-your-workflow-actions | shared | "Choose your workflow actions": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `insider` | https://academy.insiderone.com/docs/adding-advanced-filters-to-email-contacts | shared | "Adding Advanced Filters to Email Contacts": delays, filters and re-entry |
| `insider` | https://academy.insiderone.com/docs/create-double-opt-in-flow | shared | "Create a Double Opt-In Flow": flows and their triggers |
| `insider` | https://academy.insiderone.com/docs/personalize-emails-with-dynamic-content | shared | "Personalize emails with dynamic content": personalisation in messages (the Yotpo guide or partner pages mention it) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/115000250912-Understanding-custom-profile-properties | shared | "Understanding custom profile properties": custom properties and events (the Yotpo guide or partner pages mention it) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/115002774952-Guide-to-Flow-Triggers-and-Flow-Filters | shared | "Guide to Flow Triggers and Flow Filters": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/360003040052-How-to-create-a-segment-or-list-triggered-flow | shared | "How to create a segment- or list-triggered flow": segments and lists (the Yotpo guide or partner pages mention it) |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us/articles/360003057151-How-to-create-a-metric-triggered-flow | shared | "How to create a metric-triggered flow": custom properties and events (the Yotpo guide or partner pages mention it) |
| `knocommerce` | https://docs.knocommerce.com/en/articles/7039009-target-survey-by-customer-language | shared | "Target Survey by Customer Language": targeting and display rules |
| `knocommerce` | https://docs.knocommerce.com/en/articles/9252122-layering-targeting-filtering-audiences | shared | "Layering Targeting & Filtering Audiences": targeting and display rules |
| `knocommerce` | https://docs.knocommerce.com/en/articles/9252329-targeting-audiences | shared | "Targeting Audiences": targeting and display rules |
| `later` | https://help.later.com/hc/en-us/articles/27127077380375-Access-Manage-Campaigns | shared | "Access & Manage Campaigns": campaigns |
| `later` | https://help.later.com/hc/en-us/articles/34506757229591-Using-Post-Campaign-Tagging-to-Organize-and-Report-on-Content | shared | "Using Post & Campaign Tagging to Organize and Report on Content": content, rights and galleries (the Yotpo guide or partner pages mention it) |
| `later` | https://help.later.com/hc/en-us/articles/42727688274455-Add-Later-Creator-Affiliate-Links-to-Link-in-Bio | shared | "Add Later Creator Affiliate Links to Link in Bio": creators and affiliates (the Yotpo guide or partner pages mention it) |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124129-configuring-return-methods | shared | "Configuring return methods": returns, exchanges and store credit |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124131-how-to-initiate-and-manage-a-return | shared | "How to initiate and manage a return": returns, exchanges and store credit |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124223-getting-started-with-sms-notifications | shared | "Getting started with SMS notifications Modified on Wed, 20 Aug, 2025 at 10:19 AM": tracking and notifications |
| `lexer` | https://learn.lexer.io/docs/automation-rules | shared | "Automation rules": workflows: triggers and actions |
| `lexer` | https://learn.lexer.io/docs/cases-report | shared | "Cases report": dashboards and reports |
| `lexer` | https://learn.lexer.io/docs/guide-to-using-schedule | shared | "Guide to using schedule": data sync and connectors (the Yotpo guide or partner pages mention it) |
| `limespot` | https://support.limespot.com/en/articles/4753828-how-to-view-audience-segment-analytics | shared | "How to view Audience Segment analytics": targeting and display rules |
| `limespot` | https://support.limespot.com/en/articles/5392396-using-audience-segmentation-custom-events | shared | "Using audience segmentation custom events?": custom data and code (the Yotpo guide or partner pages mention it) |
| `limespot` | https://support.limespot.com/en/articles/9160423-how-to-sync-limespot-audience-segments-with-google-ads | shared | "How to sync LimeSpot audience segments with Google Ads": targeting and display rules |
| `listrak` | https://help.listrak.com/en/articles/3544105-creating-a-welcome-series-in-journey-hub | shared | "Creating a Welcome Series in Journey Hub Learn how to create a journey using the List Subscription event in Journey Hub.": segments and lists (the Yotpo guide or partner pages mention it) |
| `listrak` | https://help.listrak.com/en/articles/5195951-testing-journeys-in-journey-hub | shared | "Testing Journeys in Journey Hub Learn how to use the Test feature to test your journeys prior to activating them for contacts.": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `listrak` | https://help.listrak.com/en/articles/5472394-custom-events-in-journey-hub | shared | "Custom Events in Journey Hub Learn how to trigger a journey based on an event you determine.": custom properties and events (the Yotpo guide or partner pages mention it) |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12707618-customer-portal | shared | "Customer portal": customer portal |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/15588270-handling-subscription-renewals-that-require-3d-secure-3ds-verification | shared | "Handling subscription renewals that require 3D Secure \(3DS\) verification": recurring orders and renewals |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/15920328-volume-discounts-overview | shared | "Volume discounts overview": discount codes on subscriptions |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/1965846-building-tiers-how-they-work | shared | "Building tiers & how they work Build your tier structure, choose how customers qualify and how long a tier lasts, and launch your tiers.": referrals and VIP tiers |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/6601715-magento-adding-voucher-codes-to-your-rewards | shared | "Magento: Adding voucher codes to your rewards Let LoyaltyLion create your Magento voucher codes automatically, or generate them in Magento and import ": importing customers and balances |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/7135405-shopify-plus-reward-redeem-points-at-checkout | shared | "[Shopify Plus] Reward: Redeem points at checkout How to let customers spend points for money off inside the Shopify checkout.": points and rewards |
| `mailchimp` | https://mailchimp.com/help/audiences | shared | "Audiences": segments and lists (the Yotpo guide or partner pages mention it) |
| `mailchimp` | https://mailchimp.com/help/automation | shared | "Automation": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `mailchimp` | https://mailchimp.com/help/requirements-best-practices-audiences | shared | "Requirements and Best Practices for Audiences": segments and lists (the Yotpo guide or partner pages mention it) |
| `mesa` | https://docs.getmesa.com/readme/dashboard | shared | "Dashboard": dashboards and reports |
| `mesa` | https://docs.getmesa.com/workflow-activity | shared | "Workflow Activity": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `mesa` | https://docs.getmesa.com/workflow-builder | shared | "Workflow Builder": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `nosto` | https://help.nosto.com/en/articles/2753511-how-to-easily-create-blocks-for-content-personalization | shared | "How to easily create blocks for content personalization?": widgets and templates |
| `nosto` | https://help.nosto.com/en/articles/2933545-how-to-validate-if-customers-are-correctly-added-to-nosto-javascript-based-segments | shared | "How to validate if customers are correctly added to Nosto JavaScript based segments": custom data and code (the Yotpo guide or partner pages mention it) |
| `nosto` | https://help.nosto.com/en/articles/3018841-how-to-export-segments | shared | "How to export segments": targeting and display rules |
| `novel` | https://support.novel.com/start-guide/app-setup.md | shared | "Markdown": apps on the point of sale (the Yotpo guide or partner pages mention it) |
| `novel` | https://support.novel.com/start-guide/create-your-pass | shared | "Create your pass": passes and their fields (the Yotpo guide or partner pages mention it) |
| `novel` | https://support.novel.com/start-guide/customer-tags | shared | "Customer Tags": customers at the point of sale (the Yotpo guide or partner pages mention it) |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/360014165237-How-to-use-CSV-upload-as-an-automation-trigger | shared | "How to use CSV upload as an automation trigger": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/7867040007581-Using-custom-fields-with-decimals-in-merge-tags | shared | "Using custom fields with decimals in merge tags": personalisation in messages (the Yotpo guide or partner pages mention it) |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/8594792408733-Properties-in-custom-events | shared | "Properties in custom events": custom properties and events (the Yotpo guide or partner pages mention it) |
| `omnisend` | https://support.omnisend.com/en/articles/12569070-understand-omnisend-segment-filters | shared | "Understand Omnisend Segment Filters": segments and lists (the Yotpo guide or partner pages mention it) |
| `omnisend` | https://support.omnisend.com/en/articles/3954813-set-up-automation-workflow-settings | shared | "Set Up Automation Workflow Settings": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `omnisend` | https://support.omnisend.com/en/articles/4298431-understand-event-data-in-automation-workflows | shared | "Understand Event Data in Automation Workflows": custom properties and events (the Yotpo guide or partner pages mention it) |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/115002521171-How-to-prevent-unwanted-sync-changes-in-9-2-upgrade | shared | "How to prevent unwanted sync changes in 9.2 upgrade": data sync and connectors |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/115002944983-Episerver-Reach-Triggers-user-guide | shared | "Episerver Reach: Triggers user guide": workflows: triggers and actions |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/35923618827277-SA1639326-Inconsistent-sales-amounts-between-Abandoned-Cart-and-Online-Orders-dashboards | shared | "SA1639326 - Inconsistent sales amounts between Abandoned Cart and Online Orders dashboards": dashboards and reports |
| `order_desk` | https://help.orderdesk.com/guided-walkthroughs/products-and-inventory/how-to-sync-inventory-between-order-desk-stores | shared | "How to Sync Inventory Between Order Desk Stores": data sync and connectors (the Yotpo guide or partner pages mention it) |
| `order_desk` | https://help.orderdesk.com/guided-walkthroughs/rules-and-automations | shared | "Rules and Automations": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `order_desk` | https://help.orderdesk.com/guided-walkthroughs/rules-and-automations/how-to-create-your-first-automation | shared | "How to create Your First Automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `ordergroove` | https://docs.ordergroove.com/advanced/prepaid-renewal | shared | "Managing Prepaid Renewal Behaviors": recurring orders and renewals (the Yotpo guide or partner pages mention it) |
| `ordergroove` | https://docs.ordergroove.com/graphql/graphql-definitions/objects/discount-incentive-type | shared | "DiscountIncentiveType": discount codes on subscriptions (the Yotpo guide or partner pages mention it) |
| `ordergroove` | https://docs.ordergroove.com/lifecycle/enrollment/affiliate-codes | shared | "Tracking Affiliate Codes on Recurring Orders": recurring orders and renewals (the Yotpo guide or partner pages mention it) |
| `pagefly` | https://help.pagefly.io/page-structure-and-elements/main-use-case/direct-to-a-link-a-section-a-pop-up-an-email-address-or-a-phone-number-by-click-action | shared | "Direct to Links, Sections, Pop-ups": blocks and components (the Yotpo guide or partner pages mention it) |
| `pagefly` | https://help.pagefly.io/page-structure-and-elements/shopify-elements/custom-content/how-to-use-shopify-app-block-element-with-pagefly-section | shared | "App blocks": blocks and components (the Yotpo guide or partner pages mention it) |
| `pagefly` | https://help.pagefly.io/pages-and-sections-creation/pages/add-more-content-to-my-shopify-product-page | shared | "How to create a Product page with PageFly": product pages |
| `postpilot` | https://help.postpilot.com/knowledge/flow-triggers | shared | "Flow triggers": workflows: triggers and actions |
| `postpilot` | https://help.postpilot.com/knowledge/how-to-reactivate-and-re-sync-a-disconnected-klaviyo-segment | shared | "How to reactivate and re sync a disconnected klaviyo segment": data sync and connectors |
| `postpilot` | https://help.postpilot.com/knowledge/using-in-app-dashboard | shared | "Using in app dashboard": dashboards and reports |
| `productsup` | https://www.productsup.com/guides/business-growth-report | shared | "Business growth report": dashboards and reports |
| `reamaze` | https://support.reamaze.com/kb/advanced-settings/creating-and-using-response-templates | shared | "Response Templates (Saved Replies, Canned Responses)": macros and replies |
| `reamaze` | https://support.reamaze.com/kb/getting-started/step-4-creating-your-avatar | shared | "Step 4: Create Your Staff Profile": customer profile in the sidebar (the Yotpo guide or partner pages mention it) |
| `reamaze` | https://support.reamaze.com/kb/using-the-ai-agent/understanding-where-your-ai-agent-gets-its-answers | shared | "AI Agent Knowledge Sources & AI Corrections": AI agent knowledge and actions (the Yotpo guide or partner pages mention it) |
| `rebuy` | https://help.rebuyengine.com/en/articles/10491426-how-to-configure-customize-bundle-builder-installation-settings-guide | shared | "How to Configure & Customize Bundle Builder: Installation & Settings Guide Create unique experiences and boost AOV with Rebuy's Bundle Builder": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `rebuy` | https://help.rebuyengine.com/en/articles/14603677-bundle-builder-cart-transforms-and-items-grouping | shared | "Bundle Builder: Cart Transforms and Items Grouping Learn how Cart Transforms and Items Grouping display bundled products as grouped line items in the ": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `rebuy` | https://help.rebuyengine.com/en/articles/16152980-bundle-builder-filter-and-sorting-settings | shared | "Bundle Builder: Filter and Sorting Settings How to enable and configure product filtering and sorting in Rebuy's Bundle Builder — the available filter": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/33693661450903-How-to-translate-your-selling-plans | shared | "How to translate your selling plans": subscription products and plans (the Yotpo guide or partner pages mention it) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360008682094-Manually-process-a-recurring-order-immediately | shared | "Manually process a recurring order immediately": recurring orders and renewals (the Yotpo guide or partner pages mention it) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360034748173-Managing-subscription-discount-codes | shared | "Managing subscription discount codes": discount codes on subscriptions (the Yotpo guide or partner pages mention it) |
| `refersion` | http://support.refersion.com/en/articles/4711307-how-to-create-an-effective-affiliate-registration-page | shared | "How to Create an Effective Affiliate Registration Page": creators and affiliates (the Yotpo guide or partner pages mention it) |
| `refersion` | http://support.refersion.com/en/articles/4711449-how-to-grow-your-affiliate-network | shared | "How to Grow Your Affiliate Network?": creators and affiliates (the Yotpo guide or partner pages mention it) |
| `refersion` | http://support.refersion.com/en/articles/7035709-how-to-get-the-most-out-of-your-affiliate-program | shared | "How to Get the Most Out of Your Affiliate Program": creators and affiliates (the Yotpo guide or partner pages mention it) |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/360037988811-Segmenting-Customers-The-Complete-Filter-Guide | shared | "Segmenting Customers - The Complete Filter Guide": delays, filters and re-entry |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/52109360156052-Create-Multiple-Choice-Custom-Fields-to-Capture-Preferences-and-Segment-Contacts | shared | "Create Multiple Choice Custom Fields to Capture Preferences and Segment Contacts": custom properties and events |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/7427449223188-Getting-Started-with-Journeys | shared | "Getting Started with Journeys": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/204800567-Trigger-Happy-React-to-Every-Customer-Action | shared | "Trigger Happy - React to Every Customer Action": flows and their triggers |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/222634968-Using-merge-tags-to-display-dynamic-product-recommendations-in-the-HTML-Editor | shared | "Using merge tags to display dynamic product recommendations in the HTML Editor": personalisation in messages (the Yotpo guide or partner pages mention it) |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/360010829294-How-to-handle-subscription-preferences-with-Custom-User-Attributes | shared | "How to handle subscription preferences with Custom User Attributes": custom properties and events (the Yotpo guide or partner pages mention it) |
| `rise_ai` | http://help.rise.ai/en/articles/2396584-manage-your-gift-cards-and-store-credit | shared | "Manage your Gift Cards and Store Credit": gift cards and store credit (the Yotpo guide or partner pages mention it) |
| `rise_ai` | http://help.rise.ai/en/articles/4020903-how-to-create-an-account-creation-reward | shared | "How to Create an Account Creation Reward": points and rewards |
| `rise_ai` | http://help.rise.ai/en/articles/4020904-how-to-create-a-first-purchase-reward | shared | "How to Create a First Purchase Reward": rewards and incentives |
| `rule` | https://help.rule.io/sv/articles/349420-journey-builder-introduktion | shared | "Journey Builder - Introduktion": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `rule` | https://help.rule.io/sv/articles/349422-journey-builder-kom-igang | shared | "Journey Builder – Kom igång": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `rule` | https://help.rule.io/sv/articles/349423-kom-igang-med-preferenser-i-journey-builder | shared | "Kom igång med preferenser i Journey Builder": flows and their triggers (the Yotpo guide or partner pages mention it) |
| `rush` | https://support.rush.app/tracking-page/general/about.html | shared | "Tracking Page": tracking and notifications |
| `searchanise` | https://docs.searchanise.io/article-categories/upsell-marketing | shared | "Upsell & Marketing": recommendation widgets (the Yotpo guide or partner pages mention it) |
| `searchanise` | https://docs.searchanise.io/set-up-filters-based-on-product-options-tag-prefixes-metafields | shared | "Setting up filters based on variant options, tag prefixes, and metafields on Shopify": filters and facets |
| `searchanise` | https://docs.searchanise.io/set-up-filters-on-collections | shared | "Setting up Filters on collections": filters and facets |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/201185139-Installing-Recommendation-Widgets | shared | "Installing recommendation widgets": apps in the theme |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/360031132951-Magento-2-Extension | shared | "Magento 2 Extension": apps in the theme |
| `shopify` | https://help.shopify.com/en/manual/checkout-settings/checkout-blocks/custom-discounts/managing-custom-discounts | shared | "Managing custom discounts": discount codes |
| `shopify` | https://help.shopify.com/en/manual/customers/customer-accounts/new-customer-accounts | shared | "Customer accounts": customer accounts (the Yotpo guide or partner pages mention it) |
| `shopify` | https://help.shopify.com/en/manual/sell-in-person/getting-started/shopify-pos-from-admin/pos-ui-extensions | shared | "Pos ui extensions": apps in the theme (the Yotpo guide or partner pages mention it) |
| `shopify_flow` | https://help.shopify.com/en/manual/reports-and-analytics | shared | "Reports and analytics": dashboards and reports |
| `shopify_flow` | https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports | shared | "Shopify analytics": dashboards and reports |
| `shopify_flow` | https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/report-types/custom-reports | shared | "Customizing and managing reports": dashboards and reports |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/customers | shared | "Customers": customers at the point of sale (the Yotpo guide or partner pages mention it) |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/customers/manage-customers | shared | "Managing customers": customers at the point of sale (the Yotpo guide or partner pages mention it) |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/shopify-admin/shopify-app | shared | "Using the Shopify app": apps on the point of sale (the Yotpo guide or partner pages mention it) |
| `smile_io` | https://help.smile.io/en/articles/4036271-configure-ways-to-redeem-points | shared | "Configure ways to redeem points": points and rewards (the Yotpo guide or partner pages mention it) |
| `smile_io` | https://help.smile.io/en/articles/4036321-understand-vip-tier-milestones | shared | "Understand VIP tier milestones": referrals and VIP tiers |
| `smile_io` | https://help.smile.io/en/articles/shopify-flow-adjust-points-balance | shared | "Use Shopify Flow to adjust a customer’s points balance": importing customers and balances |
| `social_nature` | https://socialnaturehelp.zendesk.com/hc/en-us/articles/360022528374-Do-I-have-to-post-my-review-to-social-media | shared | "Do I have to post my review to social media?": content, rights and galleries (the Yotpo guide or partner pages mention it) |
| `social_nature` | https://socialnaturehelp.zendesk.com/hc/en-us/articles/360022707353-How-do-I-share-my-review-on-social-media | shared | "How do I share my review on social media?": content, rights and galleries (the Yotpo guide or partner pages mention it) |
| `sopost` | http://help.sopost.com/en/articles/12754273-comments-in-campaign-preview | shared | "Comments in campaign preview": campaigns (the Yotpo guide or partner pages mention it) |
| `stitch` | https://www.stitchdata.com/docs/replication/syncing-historical-saas-data-resetting-replication-keys | shared | "Historical SaaS data": data sync and connectors (the Yotpo guide or partner pages mention it) |
| `stitch` | https://www.stitchdata.com/docs/replication/syncing-new-additional-columns | shared | "Replicating new and additional columns": data sync and connectors (the Yotpo guide or partner pages mention it) |
| `subtotal` | https://subtotal.com/docs/guides/ios-subtotal-link | shared | "Link accounts in your iOS App": apps on the point of sale |
| `talkable` | https://docs.talkable.com/advanced_features/customer_service_portal/use_case_1 | shared | "Use case #1: Where do I find referrals?": referrals and VIP tiers (the Yotpo guide or partner pages mention it) |
| `talkable` | https://docs.talkable.com/advanced_features/passing_custom_data | shared | "Pass Custom User Data": passes and their fields |
| `talkable` | https://docs.talkable.com/campaigns/views/advocate_rewards_confirmation | shared | "Advocate Reward Confirmation Email": points and rewards |
| `tray_io` | https://tray.ai/guides/it-onboarding-automation | shared | "It onboarding automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `tray_io` | https://tray.ai/guides/lead-lifecycle-automation | shared | "Lead lifecycle automation": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `tray_io` | https://tray.ai/guides/revops-automation-risk-assessment | shared | "Which of your automations breaks first?": workflows: triggers and actions (the Yotpo guide or partner pages mention it) |
| `triple_whale` | https://kb.triplewhale.com/en/articles/12992669-create-and-schedule-email-campaigns-with-moby | shared | "Create and Schedule Email Campaigns with Moby": data sync and connectors |
| `triple_whale` | https://kb.triplewhale.com/en/articles/13042041-create-a-gen-ui-report-from-your-dashboard | shared | "Create a Gen UI Report from Your Dashboard": dashboards and reports |
| `triple_whale` | https://kb.triplewhale.com/en/articles/15458978-create-an-automation-with-moby-chat | shared | "Create an automation with Moby chat": workflows: triggers and actions |
| `vajro` | https://docs.vajro.com/en/articles/4444206-a-simple-guide-to-superfans-push-notification-reports | shared | "A Simple Guide to Superfans Push Notification Reports": push notifications |
| `vajro` | https://docs.vajro.com/en/articles/5106341-sending-out-automated-notifications | shared | "Sending Out Automated Notifications": push notifications |
| `vajro` | https://docs.vajro.com/en/articles/5137360-scheduling-mobile-app-push-notifications | shared | "Scheduling Mobile App Push Notifications": push notifications |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272749-import-entries | shared | "Import Entries": importing customers and balances |
| `virtue` | https://help.virtueimpact.com/en/articles/8264172-when-are-donations-sent-to-causes | shared | "When are donations sent to causes?": donations (the Yotpo guide or partner pages mention it) |
| `virtue` | https://help.virtueimpact.com/en/articles/8266513-can-we-choose-when-donations-are-sent-to-the-charities | shared | "Can we choose when donations are sent to the Charities?": donations (the Yotpo guide or partner pages mention it) |
| `virtue` | https://help.virtueimpact.com/en/articles/8310622-dashboard-overview | shared | "Dashboard Overview": dashboards and reports |
| `weglot` | https://support.weglot.com/article/276-how-can-i-create-a-custom-language | shared | "How can i create a custom language": custom data and code |
| `weglot` | https://support.weglot.com/article/75-wordpress-how-i-know-content-javascript-generated | shared | "Wordpress how i know content javascript generated": custom data and code |
| `weglot` | https://support.weglot.com/article/95-how-to-exclude-urls-blocks-words-from-translation | shared | "How can I exclude URLs, blocks, or words from translation?": widgets and templates (the Yotpo guide or partner pages mention it) |
| `yieldify` | http://support.yieldify.com/en/articles/5158193-targeting-triggering-user-groups | shared | "Targeting & Triggering User Groups Explaining how to make the most of targeting user groups": targeting and display rules |
| `yieldify` | http://support.yieldify.com/en/articles/5221195-session-number-targeting | shared | "Session Number Targeting Using session count": targeting and display rules |
| `yieldify` | http://support.yieldify.com/en/articles/8389561-audience-targeting | shared | "Audience Targeting Learn more about Yieldify Audiences.": targeting and display rules |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/4408833443226-Understanding-placeholder-suppression-rules-in-ticket-triggers | shared | "Understanding placeholder suppression rules in ticket triggers": rules and automations |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/4408835022490-Viewing-and-editing-your-user-profile-in-Zendesk-Support | shared | "Viewing and editing your user profile in Zendesk Support": customer profile in the sidebar |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/4408884166554-Organizing-and-managing-your-macros | shared | "Organizing and managing your macros": macros and replies |

## How each integration's mechanics articles were found

Topics: what was searched for, best first (ranked by what the Yotpo guide and partner pages talk about; the lists are in `backend/mechanics_topics.py`).

| integration | topics searched | help centre | found via | method | picked |
|---|---|---|---|---|---:|
| `addglow` | points and rewards; importing customers and balances; referrals and VIP tiers | — | — | — | 0 |
| `adobe_commerce_magento` | apps in the theme; refunds and cancelled orders; discount codes | https://experienceleague.adobe.com/en/docs | guide | pages + llms.txt | 0 |
| `adroll` | product feeds; campaigns; personalisation in messages | — | — | — | 0 |
| `adscale` | audiences; product feeds; campaigns | https://help.adscale.com/en | catalog | — | 0 |
| `aftership` | tracking and notifications; returns, exchanges and store credit | https://support.aftership.com/en | probe | pages | 3 |
| `aftership_personalization` | results, badges and merchandising; recommendation widgets; filters and facets | https://support.aftership.com/en | catalog | pages | 3 |
| `akeneo` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://help.akeneo.com/ | catalog | pages + sitemap | 3 |
| `alloy_automation` | workflows: triggers and actions; dashboards and reports; data sync and connectors | https://runalloy.com/ | homepage | sitemap | 3 |
| `amasty` | results, badges and merchandising; filters and facets; recommendation widgets | https://amasty.com/docs | guide | — | 0 |
| `ampifyme` | blocks and components; product pages; customer accounts and login | https://help.ampifyme.com/ | probe | pages + sitemap | 3 |
| `antavo` | points and rewards; referrals and VIP tiers; importing customers and balances | https://antavo.atlassian.net/ | homepage | — | 0 |
| `appbrew` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `attentive` | flows and their triggers; segments and lists; custom properties and events | https://help.attentivemobile.com/hc/en-us | catalog | zendesk-search | 3 |
| `bazaarvoice` | content, rights and galleries; review collection and requests; campaigns | https://docs.bazaarvoice.com/home/en-us | override | pages | 3 |
| `beautytap` | campaigns; product catalog and feeds; content, rights and galleries | — | — | — | 0 |
| `beeketing_boost_sales` | widgets and templates; targeting and display rules; custom data and code | — | — | — | 0 |
| `bhn_rewards` | rewards and incentives; gift cards and store credit | https://help.rybbon.net/hc/en-us | catalog | zendesk-search | 3 |
| `bigcommerce` | apps in the theme; discount codes; customer accounts | https://support.bigcommerce.com/ | guide | — | 0 |
| `blueconic` | widgets and templates; targeting and display rules; custom data and code | https://support-experiences.blueconic.com/en | catalog | — | 0 |
| `bold_commerce` | discount codes; customer accounts; apps in the theme | https://support.boldcommerce.com/en | probe | pages | 3 |
| `boostcommerce` | results, badges and merchandising; filters and facets; recommendation widgets | https://support.boostcommerce.net/en | catalog | llms.txt | 3 |
| `braze` | custom properties and events; personalisation in messages; flows and their triggers | https://www.braze.com/docs | catalog | pages | 2 |
| `brevo_pushowl` | flows and their triggers; custom properties and events; segments and lists | https://docs.pushowl.com/en | catalog | pages | 3 |
| `builder_io` | blocks and components; product pages; customer accounts and login | https://www.builder.io/ | homepage | pages + sitemap | 0 |
| `checkout` | checkout; discount codes; customer accounts | — | — | — | 0 |
| `checkout_plus` | checkout; discount codes; customer accounts | — | — | — | 0 |
| `chimeable` | content, rights and galleries; review collection and requests; campaigns | — | — | — | 0 |
| `cohley` | content, rights and galleries; creators and affiliates; campaigns | — | — | — | 0 |
| `cordial` | custom properties and events; flows and their triggers; segments and lists | https://support.cordial.com/hc/en-us | guide | zendesk-search | 3 |
| `daasity` | data sync and connectors; dashboards and reports; workflows: triggers and actions | https://help.daasity.com/ | catalog | pages | 3 |
| `daitafix` | data sync and connectors; workflows: triggers and actions; dashboards and reports | https://daitafix.com/ | homepage | — | 0 |
| `datagrail` | data subject requests; workflows: triggers and actions; data sync and connectors | https://docs.datagrail.io/ | homepage | pages | 3 |
| `dialogue` | results, badges and merchandising; recommendation widgets; widgets and templates | https://help.nowdialogue.com/en | catalog | — | 0 |
| `digioh` | widgets and templates; targeting and display rules; custom data and code | https://help.digioh.com/knowledgebase | catalog | — | 0 |
| `dixa` | customer profile in the sidebar; macros and replies; rules and automations | https://support.dixa.help/en | catalog | sitemap | 3 |
| `dondy` | flows and their triggers; workflows: triggers and actions; data sync and connectors | https://help.dondy.net/ | probe | pages + llms.txt | 3 |
| `dotdigital` | custom properties and events; personalisation in messages; flows and their triggers | https://marketing.help.dotdigital.com/en | catalog | pages | 3 |
| `dotdigital_personalization` | widgets and templates; targeting and display rules; custom data and code | https://personalization.help.dotdigital.com/en | catalog | pages | 3 |
| `drip` | segments and lists; workflows: triggers and actions; flows and their triggers | https://www.drip.com/learn/docs | catalog | — | 0 |
| `ecocart` | donations | https://support.ecocart.io/knowledge | homepage | — | 0 |
| `ecomposer` | blocks and components; product pages; customer accounts and login | https://help.ecomposer.io/docs | catalog | pages | 3 |
| `emarsys` | flows and their triggers; custom properties and events; segments and lists | https://help.emarsys.com/hc/en-us | guide | — | 0 |
| `expertvoice` | product catalog and feeds; review collection and requests; campaigns | — | — | — | 0 |
| `facebook` | content, rights and galleries; product feeds; audiences | — | — | — | 0 |
| `fast_simon` | results, badges and merchandising; filters and facets; recommendation widgets | https://www.fastsimon.com/ | homepage | — | 0 |
| `findify` | discount codes; customer accounts; apps in the theme | https://developers.findify.io/docs | catalog | — | 0 |
| `flashchat` | segments and lists; flows and their triggers; delays, filters and re-entry | — | — | — | 0 |
| `fobi` | customers at the point of sale; passes and their fields; discounts at the point of sale | — | — | — | 0 |
| `fomo` | targeting and display rules; custom data and code; widgets and templates | https://fomo.family/ | homepage | — | 0 |
| `fuego` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `fueled` | workflows: triggers and actions; data sync and connectors; dashboards and reports | — | — | — | 0 |
| `gempages` | blocks and components; product pages; customer accounts and login | https://help.gempages.net/ | catalog | pages + sitemap | 3 |
| `gladly` | customer profile in the sidebar; macros and replies; rules and automations | https://help.gladly.com/docs | catalog | pages + llms.txt | 3 |
| `glew` | dashboards and reports; data sync and connectors; workflows: triggers and actions | https://www.glew.io/ | homepage | pages + sitemap | 3 |
| `gogenerosity` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://help.gogenerosity.com/ | catalog | pages + sitemap | 0 |
| `google` | product catalog and feeds; product feeds; review collection and requests | — | — | — | 0 |
| `gorgias` | customer profile in the sidebar; rules and automations; AI agent knowledge and actions | https://docs.gorgias.com/en-US | guide | pages | 3 |
| `harbor` | points and rewards; importing customers and balances; referrals and VIP tiers | — | — | — | 0 |
| `heartland_retail_by_hyperspace` | discounts at the point of sale; customers at the point of sale; apps on the point of sale | https://hyperspace.zendesk.com/hc/en-us | homepage | zendesk-search | 2 |
| `hubspot` | flows and their triggers; custom properties and events; segments and lists | https://knowledge.hubspot.com/ | override | pages | 3 |
| `insider` | personalisation in messages; flows and their triggers; delays, filters and re-entry | https://academy.insiderone.com/docs | catalog | pages + llms.txt | 3 |
| `instagram` | content, rights and galleries; audiences; product feeds | — | — | — | 0 |
| `judge_me` | campaigns; content, rights and galleries; review collection and requests | https://judge.me/help/en | catalog | pages | 0 |
| `kimonix` | widgets and templates; targeting and display rules; custom data and code | http://help.kimonix.com/ | catalog | — | 0 |
| `klaviyo` | custom properties and events; segments and lists; flows and their triggers | https://help.klaviyo.com/hc/en-us | guide | zendesk-search | 3 |
| `klaviyo_customer_hub` | flows and their triggers; custom properties and events; segments and lists | https://help.klaviyo.com/hc/en-us | catalog | zendesk-search | 3 |
| `klevu` | results, badges and merchandising; filters and facets; recommendation widgets | https://help.klevu.com/support | catalog | — | 0 |
| `knocommerce` | widgets and templates; targeting and display rules; custom data and code | https://docs.knocommerce.com/en | catalog | pages | 3 |
| `later` | content, rights and galleries; creators and affiliates; review collection and requests | https://help.later.com/hc/en-us | homepage | zendesk-search | 3 |
| `lateshipment_com` | returns, exchanges and store credit; tracking and notifications | https://support.lateshipment.com/ | homepage | pages + sitemap | 3 |
| `lexer` | data sync and connectors; workflows: triggers and actions; dashboards and reports | https://learn.lexer.io/docs | catalog | sitemap | 3 |
| `limespot` | custom data and code; widgets and templates; targeting and display rules | https://support.limespot.com/en | catalog | pages | 3 |
| `listrak` | flows and their triggers; segments and lists; custom properties and events | https://help.listrak.com/en | catalog | pages | 3 |
| `loop_subscriptions` | discount codes on subscriptions; recurring orders and renewals; customer portal | https://help.loopwork.co/en | catalog | llms.txt | 3 |
| `loudcrowd` | content, rights and galleries; review collection and requests; campaigns | https://help.loudcrowd.com/en | catalog | — | 0 |
| `loyaltylion` | points and rewards; importing customers and balances; referrals and VIP tiers | https://help.loyaltylion.com/en | override | pages | 3 |
| `magenative` | blocks and components; product pages; customer accounts and login | https://www.magenative.com/ | homepage | — | 0 |
| `mailchimp` | flows and their triggers; segments and lists; custom properties and events | https://mailchimp.com/help | catalog | pages | 3 |
| `mesa` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://docs.getmesa.com/ | catalog | pages | 3 |
| `movable_ink` | workflows: triggers and actions; data sync and connectors; personalisation in messages | https://support.movableink.com/hc/en-us | guide | — | 0 |
| `nosto` | custom data and code; widgets and templates; targeting and display rules | https://help.nosto.com/en | homepage | pages | 3 |
| `novel` | updating passes; customers at the point of sale; passes and their fields | https://support.novel.com/ | catalog | pages | 3 |
| `ometria` | flows and their triggers; custom properties and events; personalisation in messages | https://support.ometria.com/hc/en-gb | catalog | zendesk-search | 3 |
| `omnisend` | flows and their triggers; custom properties and events; segments and lists | https://support.omnisend.com/en | catalog | pages | 3 |
| `optimizely` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://support.optimizely.com/hc/en-us | homepage | zendesk-search | 3 |
| `optimove` | custom properties and events; segments and lists; workflows: triggers and actions | https://academy.optimove.com/en | catalog | — | 0 |
| `order_desk` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://help.orderdesk.com/ | catalog | pages + llms.txt | 3 |
| `ordergroove` | discount codes on subscriptions; subscription products and plans; recurring orders and renewals | https://docs.ordergroove.com/ | probe | pages + llms.txt | 3 |
| `pagefly` | blocks and components; product pages; customer accounts and login | https://help.pagefly.io/ | catalog | pages + llms.txt | 3 |
| `pie_eye` | data subject requests | — | — | — | 0 |
| `plobal_apps` | product pages; blocks and components; customer accounts and login | https://plobalapps.freshdesk.com/support | homepage | — | 0 |
| `poq` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `postpilot` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://help.postpilot.com/knowledge | catalog | pages + sitemap | 3 |
| `postscript` | flows and their triggers; custom properties and events; segments and lists | https://help.postscript.io/hc/en-us | guide | — | 0 |
| `powerreviews` | content, rights and galleries; product catalog and feeds; review collection and requests | https://www.powerreviews.com/ | probe | — | 0 |
| `productsup` | data sync and connectors; workflows: triggers and actions; dashboards and reports | https://www.productsup.com/ | homepage | sitemap | 1 |
| `provesource` | widgets and templates; targeting and display rules; custom data and code | — | — | — | 0 |
| `reactiv` | blocks and components; product pages; customer accounts and login | https://support.reactivapp.com/en | catalog | — | 0 |
| `reamaze` | customer profile in the sidebar; AI agent knowledge and actions; macros and replies | https://support.reamaze.com/ | homepage | pages | 3 |
| `rebuy` | targeting and display rules; recommendation widgets; widgets and templates | https://help.rebuyengine.com/en | catalog | pages | 3 |
| `recharge` | recurring orders and renewals; discount codes on subscriptions; subscription products and plans | https://support.getrecharge.com/hc/en-us | guide | zendesk-search | 3 |
| `refersion` | creators and affiliates; campaigns; review collection and requests | https://support.refersion.com/en | catalog | pages | 3 |
| `remarkety` | flows and their triggers; delays, filters and re-entry; custom properties and events | https://support.remarkety.com/hc/en-us | catalog | zendesk-search | 3 |
| `rep_ai` | customer profile in the sidebar; macros and replies; rules and automations | — | — | — | 0 |
| `retention_science` | custom properties and events; personalisation in messages; flows and their triggers | https://help.retentionscience.com/hc/en-us | guide | zendesk-search | 3 |
| `rise_ai` | gift cards and store credit; rewards and incentives; points and rewards | https://help.rise.ai/en | catalog | llms.txt | 3 |
| `rule` | flows and their triggers; personalisation in messages; delays, filters and re-entry | https://help.rule.io/sv | homepage | pages | 3 |
| `rush` | returns, exchanges and store credit; tracking and notifications | https://support.rush.app/ | catalog | pages | 1 |
| `sailthru` | flows and their triggers; custom properties and events; segments and lists | — | — | — | 0 |
| `salesforce_commerce_cloud` | apps in the theme; discount codes; customer accounts | https://help.salesforce.com/ | probe | — | 0 |
| `salesforce_marketing_cloud` | flows and their triggers; custom properties and events; personalisation in messages | https://help.salesforce.com/ | guide | — | 0 |
| `searchanise` | recommendation widgets; results, badges and merchandising; filters and facets | https://docs.searchanise.io/ | probe | pages | 3 |
| `searchspring` | discount codes; customer accounts; apps in the theme | https://help.searchspring.net/hc/en-us | catalog | zendesk-search + sitemap | 2 |
| `shoelace` | results, badges and merchandising; filters and facets; recommendation widgets | — | — | — | 0 |
| `shogun` | blocks and components; product pages; customer accounts and login | https://getshogun.com/help/en | catalog | — | 0 |
| `shopeaks` | product feeds; audiences; campaigns | — | — | — | 0 |
| `shopify` | apps in the theme; customer accounts; discount codes | https://help.shopify.com/en/manual | guide | pages + sitemap | 3 |
| `shopify_flow` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shopify_plus` | apps in the theme; customer accounts; discount codes | https://help.shopify.com/en/manual | guide | pages + sitemap | 3 |
| `shopify_point_of_sale` | discounts at the point of sale; customers at the point of sale; apps on the point of sale | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shoppinggives` | donations | https://faq.shoppinggives.com/hc/en-us | guide | — | 0 |
| `siena` | customer profile in the sidebar; macros and replies; rules and automations | https://support.siena.cx/hc/en-us | catalog | — | 0 |
| `skeepers` | campaigns; content, rights and galleries; creators and affiliates | — | — | — | 0 |
| `smile_io` | points and rewards; importing customers and balances; referrals and VIP tiers | https://help.smile.io/en | catalog | pages + llms.txt | 3 |
| `social_nature` | content, rights and galleries; review collection and requests; campaigns | https://socialnaturehelp.zendesk.com/hc/en-us | homepage | zendesk-search + pages + sitemap | 2 |
| `sopost` | campaigns; content, rights and galleries; review collection and requests | https://help.sopost.com/en | homepage | pages | 1 |
| `square_pos_by_defsys` | discounts at the point of sale; customers at the point of sale; apps on the point of sale | — | — | — | 0 |
| `stellar_reviews` | review collection and requests; campaigns; product catalog and feeds | — | — | — | 0 |
| `stitch` | data sync and connectors; workflows: triggers and actions; dashboards and reports | https://www.stitchdata.com/docs | catalog | pages | 2 |
| `subtotal` | discounts at the point of sale; customers at the point of sale; apps on the point of sale | https://subtotal.com/docs | catalog | pages | 1 |
| `swapt` | customers at the point of sale; discounts at the point of sale; apps on the point of sale | — | — | — | 0 |
| `syncly` | workflows: triggers and actions; data sync and connectors; dashboards and reports | — | — | — | 0 |
| `talkable` | referrals and VIP tiers; points and rewards; importing customers and balances | https://docs.talkable.com/ | catalog | pages | 3 |
| `tapcart` | blocks and components; push notifications; product pages | https://help.tapcart.com/en | catalog | pages | 0 |
| `target` | product catalog and feeds; content, rights and galleries; review collection and requests | — | — | — | 0 |
| `teamwork_commerce` | customers at the point of sale; discounts at the point of sale; apps on the point of sale | https://www.teamworkcommerce.com/ | homepage | — | 0 |
| `tiktok_shop` | product catalog and feeds; content, rights and galleries; review collection and requests | https://partner.tiktokshop.com/doc | guide | — | 0 |
| `tray_io` | data sync and connectors; workflows: triggers and actions; dashboards and reports | https://tray.ai/ | homepage | llms.txt + sitemap | 3 |
| `treet` | donations | https://treetbrandsuccess.zendesk.com/hc/en-us | catalog | sitemap | 0 |
| `trend` | content, rights and galleries; campaigns; creators and affiliates | — | — | — | 0 |
| `triple_whale` | workflows: triggers and actions; data sync and connectors; dashboards and reports | https://kb.triplewhale.com/en | catalog | llms.txt | 3 |
| `try_review` | content, rights and galleries; review collection and requests; campaigns | — | — | — | 0 |
| `twitter` | product catalog and feeds; content, rights and galleries; review collection and requests | — | — | — | 0 |
| `vajro` | blocks and components; product pages; customer accounts and login | https://docs.vajro.com/en | probe | pages | 3 |
| `viralsweep` | points and rewards; importing customers and balances; referrals and VIP tiers | https://support.viralsweep.com/ | catalog | llms.txt + sitemap | 1 |
| `virtue` | donations; workflows: triggers and actions; data sync and connectors | https://help.virtueimpact.com/en | catalog | pages | 3 |
| `volusion` | apps in the theme; discount codes; customer accounts | — | — | — | 0 |
| `weglot` | widgets and templates; targeting and display rules; custom data and code | https://support.weglot.com/ | guide | pages + sitemap | 3 |
| `wonderment` | tracking and notifications; review collection and requests; campaigns | https://docs.wonderment.com/ | catalog | — | 0 |
| `woocommerce` | apps in the theme; discount codes; customer accounts | https://woocommerce.com/ | homepage | — | 0 |
| `yieldify` | widgets and templates; targeting and display rules; custom data and code | https://support.yieldify.com/en | probe | pages | 3 |
| `zembula` | personalisation in messages; workflows: triggers and actions; data sync and connectors | — | — | — | 0 |
| `zendesk` | customer profile in the sidebar; macros and replies; rules and automations | https://support.zendesk.com/hc/en-us | guide | zendesk-search | 3 |
| `zinrelo` | points and rewards; importing customers and balances; referrals and VIP tiers | — | — | — | 0 |

### No help centre found (37)

Add a line to `scripts/help_centres.json` (`"name": "https://help.example.com"`) and run the dry run again, or `null` to skip an integration on purpose.

- `addglow`: no help centre found at help./support./docs./knowledge.addglow.com
- `adroll`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `appbrew`: no help centre found at help./support./docs./knowledge.appbrew.tech
- `beautytap`: no help centre found at help./support./docs./knowledge.beautytap.com
- `beeketing_boost_sales`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `checkout`: no help centre found at help./support./docs./knowledge.checkoutreview.com
- `checkout_plus`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `chimeable`: no help centre found at help./support./docs./knowledge.chimeable.com
- `cohley`: no help centre found at help./support./docs./knowledge.cohley.com
- `expertvoice`: no help centre found at help./support./docs./knowledge.expertvoice.com
- `facebook`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `flashchat`: no help centre found at help./support./docs./knowledge.flashchat.ai
- `fobi`: no help centre found at help./support./docs./knowledge.fobi.ai
- `fuego`: no help centre found at help./support./docs./knowledge.fuego.io
- `fueled`: no help centre found at help./support./docs./knowledge.fueled.io
- `google`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `harbor`: no help centre found at help./support./docs./knowledge.harborloyalty.com
- `instagram`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `pie_eye`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `poq`: no help centre found at help./support./docs./knowledge.poqcommerce.com
- `provesource`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `rep_ai`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `sailthru`: no help centre found at help./support./docs./knowledge.sailthru.com
- `shoelace`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `shopeaks`: no help centre found at help./support./docs./knowledge.shopeaks.com
- `skeepers`: no help centre found at help./support./docs./knowledge.octoly.com
- `square_pos_by_defsys`: no help centre found at help./support./docs./knowledge.defsysmulticonnect.com
- `stellar_reviews`: no help centre found at help./support./docs./knowledge.stellarreviews.com
- `swapt`: no help centre found at help./support./docs./knowledge.swaptqr.com
- `syncly`: no help centre found at help./support./docs./knowledge.syncly.app
- `target`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `trend`: no help centre found at help./support./docs./knowledge.trend.io
- `try_review`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `twitter`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `volusion`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `zembula`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json
- `zinrelo`: no link to the app's own site on its catalog page or in its Yotpo guide; add its help centre to scripts/help_centres.json

### Help centre found, nothing picked (39)

- `adobe_commerce_magento`: help centre https://experienceleague.adobe.com/en/docs found, but no article on apps in the theme, refunds and cancelled orders, discount codes; pick some by hand
- `adscale`: help centre https://help.adscale.com/en found, but no article on audiences, product feeds, campaigns; pick some by hand
- `amasty`: help centre https://amasty.com/docs found, but no article on results, badges and merchandising, filters and facets, recommendation widgets; pick some by hand
- `antavo`: help centre https://antavo.atlassian.net/ found, but no article on points and rewards, referrals and VIP tiers, importing customers and balances; pick some by hand
- `bigcommerce`: help centre https://support.bigcommerce.com/ found, but no article on apps in the theme, discount codes, customer accounts; pick some by hand
- `blueconic`: help centre https://support-experiences.blueconic.com/en found, but no article on widgets and templates, targeting and display rules, custom data and code; pick some by hand
- `builder_io`: help centre https://www.builder.io/ found, but no article on blocks and components, product pages, customer accounts and login; pick some by hand
- `daitafix`: help centre https://daitafix.com/ found, but no article on data sync and connectors, workflows: triggers and actions, dashboards and reports; pick some by hand
- `dialogue`: help centre https://help.nowdialogue.com/en found, but no article on results, badges and merchandising, recommendation widgets, widgets and templates; pick some by hand
- `digioh`: help centre https://help.digioh.com/knowledgebase found, but no article on widgets and templates, targeting and display rules, custom data and code; pick some by hand
- `drip`: help centre https://www.drip.com/learn/docs found, but no article on segments and lists, workflows: triggers and actions, flows and their triggers; pick some by hand
- `ecocart`: help centre https://support.ecocart.io/knowledge found, but no article on donations; pick some by hand
- `emarsys`: help centre https://help.emarsys.com/hc/en-us found, but no article on flows and their triggers, custom properties and events, segments and lists; pick some by hand
- `fast_simon`: help centre https://www.fastsimon.com/ found, but no article on results, badges and merchandising, filters and facets, recommendation widgets; pick some by hand
- `findify`: help centre https://developers.findify.io/docs found, but no article on discount codes, customer accounts, apps in the theme; pick some by hand
- `fomo`: help centre https://fomo.family/ found, but no article on targeting and display rules, custom data and code, widgets and templates; pick some by hand
- `gogenerosity`: help centre https://help.gogenerosity.com/ found, but no article on workflows: triggers and actions, data sync and connectors, dashboards and reports; pick some by hand
- `judge_me`: help centre https://judge.me/help/en found, but no article on campaigns, content, rights and galleries, review collection and requests; pick some by hand
- `kimonix`: help centre http://help.kimonix.com/ found, but no article on widgets and templates, targeting and display rules, custom data and code; pick some by hand
- `klevu`: help centre https://help.klevu.com/support found, but no article on results, badges and merchandising, filters and facets, recommendation widgets; pick some by hand
- `loudcrowd`: help centre https://help.loudcrowd.com/en found, but no article on content, rights and galleries, review collection and requests, campaigns; pick some by hand
- `magenative`: help centre https://www.magenative.com/ found, but no article on blocks and components, product pages, customer accounts and login; pick some by hand
- `movable_ink`: help centre https://support.movableink.com/hc/en-us found, but no article on workflows: triggers and actions, data sync and connectors, personalisation in messages; pick some by hand
- `optimove`: help centre https://academy.optimove.com/en found, but no article on custom properties and events, segments and lists, workflows: triggers and actions; pick some by hand
- `plobal_apps`: help centre https://plobalapps.freshdesk.com/support found, but no article on product pages, blocks and components, customer accounts and login; pick some by hand
- `postscript`: help centre https://help.postscript.io/hc/en-us found, but no article on flows and their triggers, custom properties and events, segments and lists; pick some by hand
- `powerreviews`: help centre https://www.powerreviews.com/ found, but no article on content, rights and galleries, product catalog and feeds, review collection and requests; pick some by hand
- `reactiv`: help centre https://support.reactivapp.com/en found, but no article on blocks and components, product pages, customer accounts and login; pick some by hand
- `salesforce_commerce_cloud`: help centre https://help.salesforce.com/ found, but no article on apps in the theme, discount codes, customer accounts; pick some by hand
- `salesforce_marketing_cloud`: help centre https://help.salesforce.com/ found, but no article on flows and their triggers, custom properties and events, personalisation in messages; pick some by hand
- `shogun`: help centre https://getshogun.com/help/en found, but no article on blocks and components, product pages, customer accounts and login; pick some by hand
- `shoppinggives`: help centre https://faq.shoppinggives.com/hc/en-us found, but no article on donations; pick some by hand
- `siena`: help centre https://support.siena.cx/hc/en-us found, but no article on customer profile in the sidebar, macros and replies, rules and automations; pick some by hand
- `tapcart`: help centre https://help.tapcart.com/en found, but no article on blocks and components, push notifications, product pages; pick some by hand
- `teamwork_commerce`: help centre https://www.teamworkcommerce.com/ found, but no article on customers at the point of sale, discounts at the point of sale, apps on the point of sale; pick some by hand
- `tiktok_shop`: help centre https://partner.tiktokshop.com/doc found, but no article on product catalog and feeds, content, rights and galleries, review collection and requests; pick some by hand
- `treet`: help centre https://treetbrandsuccess.zendesk.com/hc/en-us found, but no article on donations; pick some by hand
- `wonderment`: help centre https://docs.wonderment.com/ found, but no article on tracking and notifications, review collection and requests, campaigns; pick some by hand
- `woocommerce`: help centre https://woocommerce.com/ found, but no article on apps in the theme, discount codes, customer accounts; pick some by hand

## Guides that are gone (1)

- `yieldify`: https://support.yotpo.com/docs/yieldify-integration-guide

## Detail pages with nothing documentary (13)

- `appbrew`
- `bazaarvoice`
- `beeketing_boost_sales`
- `datagrail`
- `fobi`
- `fueled`
- `instagram`
- `loyaltylion`
- `square_pos_by_defsys`
- `syncly`
- `target`
- `try_review`
- `zinrelo`

## Links proposed for two integrations (kept on the first) (7)

- https://help.klaviyo.com/hc/en-us/articles/115002774952-Guide-to-Flow-Triggers-and-Flow-Filters: `klaviyo`, also `klaviyo_customer_hub`
- https://help.klaviyo.com/hc/en-us/articles/360003040052-How-to-create-a-segment-or-list-triggered-flow: `klaviyo`, also `klaviyo_customer_hub`
- https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/sell-in-person/getting-started/shopify-pos-from-admin/pos-ui-extensions: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/customers/customer-accounts/new-customer-accounts: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/checkout-settings/checkout-blocks/custom-discounts/managing-custom-discounts: `shopify`, also `shopify_plus`
- https://support.yotpo.com/docs/social-push: `facebook`, also `twitter`

## Already in the knowledge base (16)

- https://support.yotpo.com/docs/integrating-yotpo-reviews-with-attentive (in `attentive`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-attentive (in `attentive`)
- https://docs.pushowl.com/en/articles/14075206-yotpo-reviews-integration (in `brevo_pushowl`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital (in `dotdigital`)
- https://marketing.help.dotdigital.com/en/articles/8198950-triggered-campaigns-overview (in `dotdigital`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-emarsys (in `emarsys`)
- https://support.yotpo.com/docs/klaviyo-oauth-integration-yotpo-loyalty-referrals (in `klaviyo`)
- https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo (in `klaviyo`)
- https://support.yotpo.com/docs/klaviyo-integration-guide (in `klaviyo`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak (in `listrak`)
- https://support.yotpo.com/docs/ometria-integration-guide-for-loyalty-referrals (in `ometria`)
- https://support.yotpo.com/docs/ometria-integration-guide-for-reviews (in `ometria`)
- https://support.ometria.com/hc/en-gb/articles/4800701859997-Setting-up-Yotpo-Loyalty-Referrals (in `ometria`)
- https://support.yotpo.com/docs/omnisend-integration-guide-for-yotpo-loyalty-referrals (in `omnisend`)
- https://support.yotpo.com/docs/postscript-integration-guide-for-yotpo-loyalty-referrals (in `postscript`)
- https://support.yotpo.com/docs/creating-loyalty-referrals-workflows-in-shopify-flow (in `global`)
