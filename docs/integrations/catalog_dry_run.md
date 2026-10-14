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
| proposals: partner app overviews (new) | 226 |
| guides gone (404, no renamed match) | 1 |
| detail pages with nothing documentary | 13 |
| integrations with no help centre found | 37 |
| links already in the knowledge base (skipped) | 15 |
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

Labels: Yotpo guides are pre-filled from their own header when it names one product (empty when it names both, or none). Partner pages are left empty. App overviews are pre-filled `shared`: they describe the app, not a Yotpo product. An admin confirms every label.

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

### Partner app overviews (226)

| integration | link | label | note |
|---|---|---|---|
| `adobe_commerce_magento` | https://experienceleague.adobe.com/en/docs/commerce-on-cloud/user-guide/overview | shared | about the app: "Adobe Commerce on Cloud" (overview, names the app) |
| `adobe_commerce_magento` | https://experienceleague.adobe.com/en/docs/commerce/cloud-service/overview | shared | about the app: "Adobe Commerce as a Cloud Service" (overview, names the app) |
| `adobe_commerce_magento` | https://experienceleague.adobe.com/en/docs/commerce/optimizer/overview | shared | about the app: "Adobe Commerce Optimizer" (overview, names the app) |
| `aftership` | https://support.aftership.com/en/feed/articles/15325933-get-started-with-aftership-feed-for-tiktok-shop | shared | about the app: "Get started with aftership feed for tiktok shop" (get started, names the app) |
| `aftership` | https://support.aftership.com/en/shipping/articles/15380523-what-is-aftership-shipping | shared | about the app: "What is aftership shipping" (what is, names the app) |
| `aftership` | https://support.aftership.com/en/shipping/articles/15380859-how-to-use-aftership-shipping-s-new-checkout-options | shared | about the app: "How to use aftership shipping s new checkout options" (how to use, names the app) |
| `aftership_personalization` | https://support.aftership.com/en/returns | shared | about the app: "AfterShip Returns" (in "Getting started") |
| `aftership_personalization` | https://support.aftership.com/en/shipping | shared | about the app: "AfterShip Shipping" (in "Getting started") |
| `aftership_personalization` | https://support.aftership.com/en/tracking | shared | about the app: "AfterShip Tracking" (in "Getting started") |
| `akeneo` | https://help.akeneo.com/en_US/serenity-your-first-steps-with-akeneo/1-serenity-discover-the-dashboard-in-details | shared | about the app: "Serenity discover the dashboard in details" (first steps, dashboard, names the app) |
| `akeneo` | https://help.akeneo.com/en_US/serenity-your-first-steps-with-akeneo/serenity-what-about-assets | shared | about the app: "Serenity what about assets" (first steps, about, names the app) |
| `akeneo` | https://help.akeneo.com/en_US/serenity-your-first-steps-with-akeneo/serenity-what-about-products-with-variants | shared | about the app: "Serenity what about products with variants" (first steps, about, names the app) |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/get-started | shared | about the app: "Get started" (get started, names the app) |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/introduction | shared | about the app: "Introduction" (introduction, names the app) |
| `alloy_automation` | https://runalloy.com/guides/ecommerce-operations-automation/what-is-operations-automation | shared | about the app: "What is operations automation" (what is, names the app) |
| `ampifyme` | https://help.ampifyme.com/article/4-what-is-amp | shared | about the app: "What is AMP or Accelerated Mobile Pages?" (in "Getting Started"; what is) |
| `ampifyme` | https://help.ampifyme.com/article/89-general-information | shared | about the app: "Getting Started: Onboarding Guide for PWA – Mobile App Builder" (in "Getting Started"; onboarding) |
| `ampifyme` | https://help.ampifyme.com/collection/1-the-amp-app-by-ampify | shared | about the app: "The AMP App by Ampify" (in "Getting Started") |
| `attentive` | https://help.attentive.com/hc/en-us/articles/35985714775572--1-8-Welcome-to-Attentive | shared | about the app: "(1/8) Welcome to Attentive" (in "Quick start › Onboarding"; welcome to, names the app) |
| `attentive` | https://help.attentive.com/hc/en-us/articles/36062062955668--3-8-3-steps-to-getting-started-with-SMS | shared | about the app: "(3/8) 3 steps to getting started with SMS" (in "Quick start › Onboarding"; getting started) |
| `attentive` | https://help.attentive.com/hc/en-us/articles/36168088263316--8-8-That-s-it-for-onboarding | shared | about the app: "(8/8) That’s it for onboarding!" (in "Quick start › Onboarding") |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics | shared | about the app: "Portal Basics" (basics) |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics/bazaarvoice-use-of-ai | shared | about the app: "Bazaarvoice use of AI" (basics, names the app) |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics/distribute-only | shared | about the app: "Distribute-only syndication" (basics) |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/28800081470228-How-do-I-setup-a-PIN-number-for-the-MasterCard-prepaid-reward-for-my-Mobile-Wallet | shared | about the app: "How do I setup a PIN number for the MasterCard prepaid reward for my Mobile Wallet?" (first section of the help centre, "Registering & Redeeming") |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/4402669938964-Why-do-I-need-to-verify-my-identity-to-redeem-my-prepaid-Card-VISA-and-MasterCard | shared | about the app: "Why do I need to verify my identity to redeem my prepaid Card VISA and MasterCard?" (first section of the help centre, "Registering & Redeeming") |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us/articles/4403555039636-Why-am-I-getting-Gift-is-no-longer-available-message-when-claiming-my-reward | shared | about the app: "Why am I getting "Gift is no longer available" message when claiming my reward?" (first section of the help centre, "Registering & Redeeming") |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/246839-style-guide-overview | shared | about the app: "Style Guide overview" (in "Getting Started Explore the fundamentals to create your first experience"; overview) |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/372610-ai-building-agent-overview | shared | about the app: "AI Building Agent Overview" (in "Getting Started Explore the fundamentals to create your first experience"; overview) |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/662511-onboarding-knowledge-hub | shared | about the app: "Onboarding Knowledge Hub" (in "Getting Started Explore the fundamentals to create your first experience"; onboarding) |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/10367810-boost-personalization-overview | shared | about the app: "Boost Personalization overview" (overview, names the app) |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/12981159-translation-overview-boost-turbo | shared | about the app: "Translation Overview \(Boost Turbo\)" (overview, names the app) |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9362430-introduction-to-boost-templates-widgets | shared | about the app: "Introduction to Boost Templates & Widgets" (introduction, names the app) |
| `braze` | https://www.braze.com/docs/user_guide/brazeai | shared | about the app: "BrazeAI overview" (overview) |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/15589860-toll-free-number-tfn-verification-complete-guide | shared | about the app: "Toll-Free Number (TFN) Verification - Complete Guide Everything you need to verify a toll-free number for SMS to the US and Canada: required informati" (in "Getting Started Get started with web push notifications and PushOwl 3 authors") |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/2317637-what-are-web-push-notifications | shared | about the app: "What are Web Push Notifications? Discovering a new way of marketing" (in "Getting Started Get started with web push notifications and PushOwl 3 authors") |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/3421426-pushowl-101 | shared | about the app: "PushOwl 101 Understand what web push notifications are and what PushOwl does" (in "Getting Started Get started with web push notifications and PushOwl 3 authors"; 101, names the app) |
| `builder_io` | https://www.builder.io/c/docs/get-started-fusion | shared | about the app: "Code Docs" (get started) |
| `builder_io` | https://www.builder.io/c/docs/get-started-publish | shared | about the app: "Content Docs" (get started) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/360000304831-Cordial-glossary | shared | about the app: "Cordial glossary" (in "Get started with Cordial › Cordial basics"; glossary, names the app) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/360001880452-Welcome-to-Cordial | shared | about the app: "Welcome to Cordial" (in "Get started with Cordial › Cordial basics"; welcome to, names the app) |
| `cordial` | https://support.cordial.com/hc/en-us/articles/360002050511-Get-started-for-marketers | shared | about the app: "Get started: for marketers" (in "Get started with Cordial › Cordial basics") |
| `daasity` | https://help.daasity.com/core-concepts/audiences-reverse-elt/audiences-overview | shared | about the app: "Create Your First Audience →" (overview, concepts) |
| `daasity` | https://help.daasity.com/core-concepts/data-models/unified-schemas/unified-schema-introduction | shared | about the app: "unified models" (introduction, concepts) |
| `daasity` | https://help.daasity.com/getting-started/quickstart-guides/homepage-kpi-dashboard | shared | about the app: "Learn about Home Dashboard →" (getting started, dashboard) |
| `datagrail` | https://docs.datagrail.io/docs/overview/user-management/managing-users | shared | about the app: "Platform Overview" (overview) |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/getting-started | shared | about the app: "Request Manager" (getting started) |
| `datagrail` | https://docs.datagrail.io/docs/vera/overview | shared | about the app: "Vera" (overview) |
| `dixa` | https://support.dixa.help/en/articles/2161-queue-settings-overview | shared | about the app: "Queue settings overview" (overview) |
| `dixa` | https://support.dixa.help/en/articles/252-team-overview | shared | about the app: "Team overview" (overview) |
| `dixa` | https://support.dixa.help/en/articles/604-an-introduction-to-dixa-messenger | shared | about the app: "An introduction to dixa messenger" (introduction, names the app) |
| `dondy` | https://help.dondy.net/start-here/8tTwAB5stRvombapghAKji/choose-your-whatsapp-setup/8rDHseRyfXNZK7ZLvCVmnk | shared | about the app: "Choose your WhatsApp Setup" (in "Start Here"; start here) |
| `dondy` | https://help.dondy.net/start-here/8tTwAB5stRvombapghAKji/install-dondy-on-shopify/8qiPY281VFmM6phwA7YGCz | shared | about the app: "Install Dondy on Shopify" (in "Start Here"; start here, names the app) |
| `dondy` | https://help.dondy.net/start-here/8tTwAB5stRvombapghAKji/what-dondy-does-for-your-shopify-store-/8qiPY281VEvnJqfzsTnazZ | shared | about the app: "What Dondy does for your Shopify store" (in "Start Here"; start here, names the app) |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198705-welcome-to-dotdigital-marketing | shared | about the app: "Welcome to Dotdigital Marketing" (in "Get started Get to grips with the fundamentals of Dotdigital Marketing. 2 authors"; welcome to, names the app) |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198706-get-started-with-contacts | shared | about the app: "Get started with contacts" (in "Get started Get to grips with the fundamentals of Dotdigital Marketing. 2 authors"; get started) |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198713-get-started-with-analytics | shared | about the app: "Get started with analytics" (in "Get started Get to grips with the fundamentals of Dotdigital Marketing. 2 authors"; get started) |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8518834-dotdigital-personalization-system-overview | shared | about the app: "Dotdigital Personalization system overview" (in "Get started Get to grips with the fundamentals of Dotdigital Personalization."; overview, names the app) |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8523242-introduction-to-trigger-programs | shared | about the app: "Introduction to trigger programs" (in "Get started Get to grips with the fundamentals of Dotdigital Personalization."; introduction) |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8937229-basic-account-configuration | shared | about the app: "Basic account configuration" (in "Get started Get to grips with the fundamentals of Dotdigital Personalization.") |
| `ecomposer` | https://help.ecomposer.io/docs/ecomposer-editor/section | shared | about the app: "Section Overview" (overview, names the app) |
| `ecomposer` | https://help.ecomposer.io/docs/ecomposer-shopline/quick-start | shared | about the app: "Quick start" (quick start, names the app) |
| `ecomposer` | https://help.ecomposer.io/docs/getting-started/dashboard-settings | shared | about the app: "EComposer App Dashboard Settings" (getting started, dashboard, names the app) |
| `gempages` | https://help.gempages.net/articles/introduction-to-gempages | shared | about the app: "Introduction to gempages" (introduction, names the app) |
| `gempages` | https://help.gempages.net/articles/overview-gempages-dashboard | shared | about the app: "Overview gempages dashboard" (overview, dashboard, names the app) |
| `gempages` | https://help.gempages.net/articles/overview-gempages-editor | shared | about the app: "Overview gempages editor" (overview, names the app) |
| `gladly` | https://help.gladly.com/docs/agents | shared | about the app: "How to use Gladly as an Agent" (how to use, names the app) |
| `gladly` | https://help.gladly.com/docs/new-to-gladly-ai-start-here | shared | about the app: "New to Gladly (AI)? Start Here" (start here, names the app) |
| `gladly` | https://help.gladly.com/docs/what-is-gladly-ai | shared | about the app: "What is Gladly AI" (what is, names the app) |
| `glew` | https://www.glew.io/articles/3-easy-steps-to-get-started-with-predictive-marketing | shared | about the app: "Easy steps to get started with predictive marketing" (get started) |
| `glew` | https://www.glew.io/articles/basics-ecommerce-inventory-depletion-know-right-time-reorder | shared | about the app: "Basics ecommerce inventory depletion know right time reorder" (basics) |
| `glew` | https://www.glew.io/articles/creating-an-annual-report-how-to-use-ecommerce-data-to-gain-insights-for-next-year | shared | about the app: "Creating an annual report how to use ecommerce data to gain insights for next year" (how to use) |
| `gogenerosity` | https://help.gogenerosity.com/what-is-a-corporate-donation-2 | shared | about the app: "What is a corporate donation 2" (what is) |
| `gogenerosity` | https://help.gogenerosity.com/what-is-gogenerositys-social-media-support-and-whats-the-point | shared | about the app: "What is gogenerositys social media support and whats the point" (what is) |
| `gogenerosity` | https://help.gogenerosity.com/what-is-my-pay-it-forward-balance-1 | shared | about the app: "What is my pay it forward balance 1" (what is) |
| `gorgias` | https://docs.gorgias.com/en-US/articles/getting-started-with-ai-agent-294725 | shared | about the app: "Getting Started with AI Agent" (in "AI Agent & automation features"; getting started) |
| `gorgias` | https://docs.gorgias.com/en-US/getting-started-for-new-Gorgias-users-7524978 | shared | about the app: "Getting started for new Gorgias users" (in "Get started"; getting started, names the app) |
| `gorgias` | https://docs.gorgias.com/en-US/how-to-use-gorgias-a-quick-start-guide-5705504 | shared | about the app: "How to use Gorgias: a quick start guide" (in "Get started"; quick start, names the app) |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/360009221153-Shopify-Integration-Getting-Started | shared | about the app: "Shopify Integration: Getting Started" (search "getting started with heartlandretailbyhyperspace"; getting started) |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/360009238013-Salesforce-Integration-Getting-Started | shared | about the app: "Salesforce Integration: Getting Started" (search "getting started with heartlandretailbyhyperspace"; getting started) |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/42430249949723-DoorDash-Getting-Started | shared | about the app: "DoorDash - Getting Started" (search "getting started with heartlandretailbyhyperspace"; getting started) |
| `hubspot` | https://knowledge.hubspot.com/da/get-started/hubspot-glossary | shared | about the app: "Hubspot glossary" (get started, glossary, names the app) |
| `hubspot` | https://knowledge.hubspot.com/es/account-management/understand-how-to-use-hubspot-credits | shared | about the app: "Understand how to use hubspot credits" (how to use, names the app) |
| `hubspot` | https://knowledge.hubspot.com/it/account/get-started-with-hubspot-crm | shared | about the app: "Get started with hubspot crm" (get started, names the app) |
| `insider` | https://academy.insiderone.com/v1/docs/introduction-to-architect | shared | about the app: "Architect" (introduction) |
| `insider` | https://academy.insiderone.com/v1/docs/shopping-agent-overview | shared | about the app: "Shopping Agent" (overview) |
| `insider` | https://academy.insiderone.com/v1/docs/support-agent-overview | shared | about the app: "Support Agent" (overview) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/115005076767-Getting-started-with-Klaviyo-onsite-tracking | shared | about the app: "Getting started with Klaviyo onsite tracking" (search "getting started with klaviyo"; getting started, names the app) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/15937542819355-Getting-started-with-Klaviyo-Reviews | shared | about the app: "Getting started with Klaviyo Reviews" (search "getting started with klaviyo"; getting started, names the app) |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/360045726811-Getting-started-with-Klaviyo-APIs | shared | about the app: "Getting started with Klaviyo APIs" (search "getting started with klaviyo"; getting started, names the app) |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us/articles/13267004984859-How-to-build-an-analytics-or-overview-dashboard | shared | about the app: "How to build an analytics or overview dashboard" (search "klaviyocustomerhub overview"; overview, dashboard) |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us/articles/28474458127899-How-to-use-the-conversion-overview-dashboard | shared | about the app: "How to use the conversion overview dashboard" (search "klaviyocustomerhub overview"; overview, dashboard) |
| `klevu` | https://support.klevu.com/hc/en-us/articles/39396917109147-Integrating-Klevu-on-a-New-Store | shared | about the app: "Integrating Klevu on a New Store" (in "Get Started › Smart Search") |
| `klevu` | https://support.klevu.com/hc/en-us/articles/39396934251035-Getting-started-with-Visual-Category-Merchandising | shared | about the app: "Getting started with Visual Category Merchandising" (in "Get Started › Smart Category Merchandising"; getting started) |
| `klevu` | https://support.klevu.com/hc/en-us/articles/39396953321627-Getting-Started | shared | about the app: "Getting Started" (in "Get Started › Smart Recommendations"; getting started) |
| `knocommerce` | https://docs.knocommerce.com/en/articles/12844246-registering-multiple-stores-on-shopify | shared | about the app: "Registering Multiple Stores on Shopify" (in "Getting Started Set up your account and launch your first survey in minutes.") |
| `knocommerce` | https://docs.knocommerce.com/en/articles/5555408-creating-your-first-survey | shared | about the app: "Creating your First Survey" (in "Getting Started Set up your account and launch your first survey in minutes.") |
| `knocommerce` | https://docs.knocommerce.com/en/articles/8677976-register-a-knocommerce-account | shared | about the app: "Register a KnoCommerce Account" (in "Getting Started Set up your account and launch your first survey in minutes.") |
| `later` | https://help.later.com/hc/en-us/articles/1500010572781-Schedule-Copy-Posts-With-Later-on-the-Web | shared | about the app: "Schedule & Copy Posts With Later on the Web" (in "Getting Started › Getting Started Guides") |
| `later` | https://help.later.com/hc/en-us/articles/360042771474-Access-Organize-Your-Media-Library | shared | about the app: "Access & Organize Your Media Library" (in "Getting Started › Getting Started Guides") |
| `later` | https://help.later.com/hc/en-us/articles/360043246993-Getting-Started-With-Later-Social | shared | about the app: "Getting Started With Later Social" (in "Getting Started › Getting Started Guides"; getting started, names the app) |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124140-what-is-lateshipment-com-s-delivery-experience-management- | shared | about the app: "What is lateshipment com s delivery experience management" (what is, names the app) |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124170-what-is-lateshipment-com-oneprotect- | shared | about the app: "What is lateshipment com oneprotect" (what is, names the app) |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124207-what-is-lateshipment-com- | shared | about the app: "What is lateshipment com" (what is, names the app) |
| `lexer` | https://learn.lexer.io/docs/activity-overview | shared | about the app: "Activity overview" (overview) |
| `lexer` | https://learn.lexer.io/docs/lexer-javascript-tag-basics | shared | about the app: "Lexer javascript tag basics" (basics, names the app) |
| `lexer` | https://learn.lexer.io/docs/welcome-to-lexer | shared | about the app: "Welcome to lexer" (welcome to, names the app) |
| `limespot` | https://support.limespot.com/en/articles/8751529-getting-started-with-product-bundles-discounts | shared | about the app: "Getting started with Product Bundles Discounts" (in "Personalized Discounts Learn how to use personalized discounts per product bundle and audience segment"; getting started) |
| `limespot` | https://support.limespot.com/en/articles/8851929-add-your-bundle-discounts-to-the-designer-and-publish | shared | about the app: "Add your bundle discounts to the Designer and publish" (in "Personalized Discounts Learn how to use personalized discounts per product bundle and audience segment") |
| `limespot` | https://support.limespot.com/en/articles/8852240-how-to-create-product-bundles | shared | about the app: "How to create product bundles" (in "Personalized Discounts Learn how to use personalized discounts per product bundle and audience segment") |
| `listrak` | https://help.listrak.com/en/articles/12159434-getting-started-with-listrak-s-client-support-portal | shared | about the app: "Getting Started with Listrak's Client Support Portal Learn how to setup your account and submit a support request in Listrak's Client Support portal" (in "Getting Started with Listrak Learn the basics of the Listrak Application such as: adjusting account settings, branding your account, creating lists, b"; getting started, names the app) |
| `listrak` | https://help.listrak.com/en/articles/7039189-listrak-solution-glossary | shared | about the app: "Listrak Solution Glossary" (in "Getting Started with Listrak Learn the basics of the Listrak Application such as: adjusting account settings, branding your account, creating lists, b"; glossary, names the app) |
| `listrak` | https://help.listrak.com/en/articles/9261024-mobile-app-push-enablement-guide | shared | about the app: "Mobile App Push Enablement Guide Learn what is required to begin sending mobile app push messages from within the platform." (in "Mobile App Push Notifications Learn the basics of Mobile App Push Notifications setting up your mobile app, sending an app notification, reporting das"; what is) |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12657742-subscription-overview | shared | about the app: "Subscription overview Learn how to create and manage different subscription types in Loop to drive recurring revenue and enhance customer retention." (in "Getting started"; overview, names the app) |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12703816-getting-started-with-loop | shared | about the app: "Getting started with Loop Learn how to set up, grow, and manage subscriptions with Loop while reducing churn and integrating essential apps." (in "Getting started"; getting started, names the app) |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/15477016-getting-started-with-loop-loyalty | shared | about the app: "Getting started with Loop Loyalty" (getting started, names the app) |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/4771488-welcome-to-loyaltylion | shared | about the app: "Welcome to LoyaltyLion! 🦁 What to set up first, how your customers use the program, and where to find everything" (in "Getting Started Set up your loyalty program, bring your existing data across, and get it live. F By Jason and 1 other 2 authors"; welcome to, names the app) |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/8102858-small-business-plan-overview | shared | about the app: "Small Business plan overview What your Small Business plan includes, and the features you can add to it" (in "Getting Started Set up your loyalty program, bring your existing data across, and get it live. F By Jason and 1 other 2 authors"; overview, features) |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/8102883-classic-advanced-plus-plans-overview | shared | about the app: "Classic, Advanced & Plus plans overview What your Classic, Advanced or Plus plan includes, and where to find each part of it" (in "Getting Started Set up your loyalty program, bring your existing data across, and get it live. F By Jason and 1 other 2 authors"; overview) |
| `mailchimp` | https://mailchimp.com/help/about-sms-marketing | shared | about the app: "About SMS Marketing with Mailchimp" (about, names the app) |
| `mailchimp` | https://mailchimp.com/help/getting-started | shared | about the app: "Getting Started" (getting started) |
| `mailchimp` | https://mailchimp.com/help/getting-started-tags | shared | about the app: "Getting Started with Tags" (getting started) |
| `mesa` | https://docs.getmesa.com/readme | shared | about the app: "Welcome to MESA" (welcome to, names the app) |
| `mesa` | https://docs.getmesa.com/readme/core-concepts | shared | about the app: "Core Concepts" (concepts) |
| `mesa` | https://docs.getmesa.com/readme/dashboard | shared | about the app: "Dashboard" (dashboard) |
| `nosto` | https://help.nosto.com/en/articles/1616950-asynchronous-script-loading | shared | about the app: "Asynchronous Script Loading" (in "Get Started Introduce yourself how to get started with Nosto today! By Dan and 1 other 2 authors") |
| `nosto` | https://help.nosto.com/en/articles/617973-introduction-to-nosto | shared | about the app: "Introduction To Nosto" (in "Get Started Introduce yourself how to get started with Nosto today! By Dan and 1 other 2 authors"; introduction, names the app) |
| `nosto` | https://help.nosto.com/en/articles/617994-adding-embed-script | shared | about the app: "Adding Embed Script" (in "Get Started Introduce yourself how to get started with Nosto today! By Dan and 1 other 2 authors") |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/12052983276445-Coupon-codes | shared | about the app: "Coupon codes" (in "Setting up campaigns › Coupon pools") |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/12053068297885-Fixed-coupon-codes | shared | about the app: "Fixed coupon codes" (in "Setting up campaigns › Coupon pools") |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/12053451731613-CSV-coupon-codes | shared | about the app: "CSV coupon codes" (in "Setting up campaigns › Coupon pools") |
| `omnisend` | https://support.omnisend.com/en/articles/1279355-omnisend-setup-what-to-do-before-you-begin | shared | about the app: "Omnisend Setup: What to Do Before You Begin" (in "Onboarding: Omnisend Basics Learn how to get started with Omnisend 2 authors") |
| `omnisend` | https://support.omnisend.com/en/articles/1279394-email-campaign-quick-start-guide | shared | about the app: "Email Campaign: Quick Start Guide" (in "Onboarding: Omnisend Basics Learn how to get started with Omnisend 2 authors"; quick start) |
| `omnisend` | https://support.omnisend.com/en/articles/8172193-get-started-with-omnisend | shared | about the app: "Get Started with Omnisend" (in "Onboarding: Omnisend Basics Learn how to get started with Omnisend 2 authors"; get started, names the app) |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/115002944183-What-is-a-product-feed | shared | about the app: "What is a product feed" (what is) |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/115002944523-What-is-your-QA-Quality-Assurance-process | shared | about the app: "What is your qa quality assurance process" (what is) |
| `optimizely` | https://support.optimizely.com/hc/en-us/articles/5186619622285-Overview-of-Content-Indexing | shared | about the app: "Overview of Content Indexing" (search "optimizelyzaius overview"; overview) |
| `order_desk` | https://help.orderdesk.com/start-here/getting-started-series | shared | about the app: "Getting Started Series" (getting started) |
| `order_desk` | https://help.orderdesk.com/start-here/getting-started-video-series | shared | about the app: "Getting Started Video Series" (getting started) |
| `order_desk` | https://help.orderdesk.com/start-here/learn-the-basics | shared | about the app: "Learn the basics" (start here) |
| `ordergroove` | https://docs.ordergroove.com/getting-started/app-embed | shared | about the app: "Installing Ordergroove with App Embed" (getting started, names the app) |
| `ordergroove` | https://docs.ordergroove.com/getting-started/os2-theme | shared | about the app: "Install Ordergroove on an Online Store 2.0 Theme" (getting started, names the app) |
| `ordergroove` | https://docs.ordergroove.com/getting-started/sandbox-store | shared | about the app: "Setting up a Sandbox Store" (getting started, setting up) |
| `pagefly` | https://help.pagefly.io/getting-started/getting-started | shared | about the app: "Overview" (getting started) |
| `pagefly` | https://help.pagefly.io/getting-started/quick-start | shared | about the app: "Quick start" (getting started) |
| `pagefly` | https://help.pagefly.io/pagefly-affiliate-program/affiliate-dos-and-donts | shared | about the app: "Affiliate Success: Dos & Don'ts - Everything to Know about Becoming a Successful PageFly Affiliate" (about, names the app) |
| `postpilot` | https://help.postpilot.com/knowledge/how-to-use-sitematch-anonymous-site-visitor | shared | about the app: "How to use sitematch anonymous site visitor" (how to use) |
| `postpilot` | https://help.postpilot.com/knowledge/setting-up-mailmatch-segments | shared | about the app: "Setting up mailmatch segments" (setting up) |
| `postpilot` | https://help.postpilot.com/knowledge/using-in-app-dashboard | shared | about the app: "Using in app dashboard" (dashboard) |
| `productsup` | https://www.productsup.com/de/guides/guide-to-seller-and-vendor-onboarding | shared | about the app: "Guide to seller and vendor onboarding" (onboarding) |
| `productsup` | https://www.productsup.com/guides/supplier-onboarding-guide | shared | about the app: "Supplier onboarding guide" (onboarding) |
| `productsup` | https://www.productsup.com/guides/thank-you-supplier-onboarding-guide | shared | about the app: "Thank you supplier onboarding guide" (onboarding) |
| `reamaze` | https://support.reamaze.com/kb/automation/getting-started-with-re-amaze-chatbots | shared | about the app: "Getting Started with Re:amaze Chatbots" (getting started, names the app) |
| `reamaze` | https://support.reamaze.com/kb/getting-started/what-is-re-amaze-and-is-right-for-me | shared | about the app: "What Is Re:amaze and Is It Right for Me?" (getting started, names the app) |
| `reamaze` | https://support.reamaze.com/kb/using-the-ai-agent/how-to-use-the-re-amaze-ai-agent | shared | about the app: "AI Agent: Overview and Setup" (overview, names the app) |
| `rebuy` | https://help.rebuyengine.com/en/articles/10552414-rebuy-merchant-success-program-overview | shared | about the app: "Rebuy Merchant Success Program Overview" (overview, names the app) |
| `rebuy` | https://help.rebuyengine.com/en/articles/10592445-getting-started-with-rebuy-s-bundle-builder-overview-benefits | shared | about the app: "Getting Started with Rebuy’s Bundle Builder: Overview & Benefits" (getting started, names the app) |
| `rebuy` | https://help.rebuyengine.com/en/articles/11698129-rebuy-premium-support-overview | shared | about the app: "Rebuy Premium Support Overview" (overview, names the app) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/25275129376535-Getting-started-with-Recharge-pre-built-flows-in-Klaviyo | shared | about the app: "Getting started with recharge pre built flows in klaviyo" (getting started, names the app) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/25276191673751-How-to-use-Recharge-pre-built-flows-in-Klaviyo | shared | about the app: "How to use recharge pre built flows in klaviyo" (how to use, names the app) |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360056632214-Getting-started-with-Recharge | shared | about the app: "Getting started with recharge" (getting started, names the app) |
| `refersion` | http://support.refersion.com/en/articles/1064046-how-to-use-the-affiliate-portal | shared | about the app: "How To Use The Affiliate Portal" (in "For Affiliates How to get started with Refersion as an Affiliate, plus answers to your top questions about connecting with merchants, getting paid, an"; how to use) |
| `refersion` | http://support.refersion.com/en/articles/2806309-about-the-refersion-marketplace-dashboard | shared | about the app: "About the Refersion Marketplace Dashboard" (in "For Affiliates How to get started with Refersion as an Affiliate, plus answers to your top questions about connecting with merchants, getting paid, an"; dashboard, names the app) |
| `refersion` | http://support.refersion.com/en/articles/5819978-getting-started-with-unified-payments-affiliates | shared | about the app: "Getting Started with Unified Payments (Affiliates)" (in "For Affiliates How to get started with Refersion as an Affiliate, plus answers to your top questions about connecting with merchants, getting paid, an"; getting started) |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/217945663-Introduction-guide-to-Remarkety | shared | about the app: "Introduction guide to Remarkety" (search "remarkety overview"; introduction, names the app) |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/23698399807124-How-to-Use-the-Email-and-SMS-Subscription-Popup-Form | shared | about the app: "How to Use the Email and SMS Subscription Popup Form" (search "getting started with remarkety"; how to use) |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/360053912632-Getting-Started-with-Remarkety-Overview | shared | about the app: "Getting Started with Remarkety Overview" (search "getting started with remarkety"; getting started, names the app) |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/115008521628-Getting-Started-Guide | shared | about the app: "Getting Started Guide" (in "Getting Started                                                                        › Start Here"; getting started) |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/360001867334-JavaScript-overview | shared | about the app: "JavaScript overview" (in "Onboarding Resources › JavaScript Setup"; overview) |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/360001874554-User-interaction-events-101 | shared | about the app: "User interaction events 101" (in "Onboarding Resources › JavaScript Setup"; 101) |
| `rise_ai` | http://help.rise.ai/en/articles/2233671-rise-features-and-their-benefits | shared | about the app: "Rise Features and Their Benefits" (features, names the app) |
| `rise_ai` | http://help.rise.ai/en/articles/5682663-how-to-use-the-bulk-loyalty-card-tool | shared | about the app: "How to Use the Bulk Loyalty Card Tool" (how to use) |
| `rise_ai` | http://help.rise.ai/en/articles/5682749-how-to-use-the-bulk-gift-card-tool | shared | about the app: "How to Use the Bulk Gift Card Tool" (how to use) |
| `rush` | https://support.rush.app/getting-started-with-rush.html | shared | about the app: "Getting Started With Rush" (getting started, names the app) |
| `rush` | https://support.rush.app/shipments/about/general.html | shared | about the app: "Shipments" (about) |
| `rush` | https://support.rush.app/tracking-page/general/about.html | shared | about the app: "Tracking Page" (about) |
| `searchanise` | https://docs.searchanise.io/quick-start-shopify | shared | about the app: "Quick Start on Shopify" (quick start) |
| `searchanise` | https://docs.searchanise.io/set-up-filters-based-on-product-options-tag-prefixes-metafields | shared | about the app: "Setting up filters based on variant options, tag prefixes, and metafields on Shopify" (setting up) |
| `searchanise` | https://docs.searchanise.io/set-up-filters-on-collections | shared | about the app: "Setting up Filters on collections" (setting up) |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/115003179283-Introduction-to-Searchspring | shared | about the app: "Introduction to Searchspring" (search "getting started with searchspring"; introduction, names the app) |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/115003610063-Management-Console-Overview | shared | about the app: "Management Console Overview" (search "getting started with searchspring"; overview) |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/36052809596187-Implementations-What-We-Needed-To-Get-Started | shared | about the app: "Implementations: What We Needed To Get Started" (search "getting started with searchspring"; get started) |
| `shopify` | https://help.shopify.com/en/manual/intro-to-shopify | shared | about the app: "Intro to Shopify" (intro to, names the app) |
| `shopify` | https://help.shopify.com/en/manual/intro-to-shopify/initial-setup | shared | about the app: "Getting set up to start selling" (intro to, names the app) |
| `shopify` | https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/new-to-shopify-checklists/general-checklist | shared | about the app: "Checklist for starting a store" (intro to, names the app) |
| `smile_io` | https://help.smile.io/en/articles/4036257-customer-email-overview | shared | about the app: "Understand customer emails" (overview) |
| `social_nature` | https://socialnaturehelp.zendesk.com/hc/en-us/articles/360022527254-Is-Social-Nature-free-to-join | shared | about the app: "Is Social Nature free to join?" (first section of the help centre, "How to become a Social Nature Member") |
| `social_nature` | https://socialnaturehelp.zendesk.com/hc/en-us/articles/360022706053-What-s-Social-Nature | shared | about the app: "What’s Social Nature?" (first section of the help centre, "How to become a Social Nature Member") |
| `social_nature` | https://socialnaturehelp.zendesk.com/hc/en-us/articles/9171398180123-How-can-I-refer-friends-or-family-to-Social-Nature | shared | about the app: "How can I refer friends or family to Social Nature?" (first section of the help centre, "How to become a Social Nature Member") |
| `sopost` | http://help.sopost.com/en/articles/12099184-about-sopost-licence-tiers | shared | about the app: "About SoPost licence tiers" (in "Getting started The SoPost basics By David 1 author"; about, names the app) |
| `sopost` | http://help.sopost.com/en/articles/8011063-example-custom-questions | shared | about the app: "Example Custom Questions" (in "Onboarding Documents to guide campaign set up M By Megan 1 author") |
| `stitch` | https://www.stitchdata.com/docs/getting-started/basic-concepts-system-overview | shared | about the app: "Basic concepts & system overview" (getting started, concepts) |
| `stitch` | https://www.stitchdata.com/docs/getting-started/set-up-stitch-data-pipeline | shared | about the app: "Set up your Stitch data pipeline" (getting started, set up your, names the app) |
| `stitch` | https://www.stitchdata.com/docs/getting-started/understanding-stitch-usage | shared | about the app: "Understand your Stitch row usage" (getting started, names the app) |
| `subtotal` | https://subtotal.com/docs/concepts | shared | about the app: "Concepts" (concepts) |
| `subtotal` | https://subtotal.com/docs/guides/getting-started | shared | about the app: "Getting Started" (getting started) |
| `subtotal` | https://subtotal.com/docs/subtotal-dashboard | shared | about the app: "Subtotal Dashboard" (dashboard, names the app) |
| `talkable` | https://docs.talkable.com/advanced_features/customer_service_portal/overview | shared | about the app: "Overview" (overview, features) |
| `talkable` | https://docs.talkable.com/campaigns/campaign_placements/loyalty_dashboard | shared | about the app: "Loyalty Dashboard Placement" (dashboard) |
| `talkable` | https://docs.talkable.com/mcp_server/getting_started | shared | about the app: "Getting Started" (getting started) |
| `tapcart` | https://help.tapcart.com/en/articles/11120041-welcome-to-tapcart | shared | about the app: "Welcome to Tapcart!" (welcome to, names the app) |
| `tray_io` | https://tray.ai/guides/it-onboarding-automation | shared | about the app: "It onboarding automation" (onboarding) |
| `treet` | https://treetbrandsuccess.zendesk.com/hc/en-us/articles/14616466177687-Fulfilling-Treet-Orders-from-your-Shopify-Fulfillment-Dashboard | shared | about the app: "Fulfilling treet orders from your shopify fulfillment dashboard" (dashboard, names the app) |
| `treet` | https://treetbrandsuccess.zendesk.com/hc/en-us/articles/17852766699799-Payouts-and-Accounting-Overview | shared | about the app: "Payouts and Accounting Overview" (search "treet overview"; overview) |
| `treet` | https://treetbrandsuccess.zendesk.com/hc/en-us/articles/43511282618519-Bloomreach-Customer-Segmentation-Setup-Guide | shared | about the app: "Bloomreach Customer Segmentation Setup Guide" (search "getting started with treet"; setup guide) |
| `triple_whale` | https://kb.triplewhale.com/en/articles/11013303-what-is-the-triple-pixel | shared | about the app: "What is the Triple Pixel?" (what is, names the app) |
| `triple_whale` | https://kb.triplewhale.com/en/articles/13174572-what-is-triple-whale-labs | shared | about the app: "What is Triple Whale Labs?" (what is, names the app) |
| `triple_whale` | https://kb.triplewhale.com/en/articles/13430726-how-to-use-ai-visibility-in-triple-whale | shared | about the app: "How to Use AI Visibility in Triple Whale" (how to use, names the app) |
| `vajro` | https://docs.vajro.com/en/articles/15616365-how-to-hide-vendor-and-brand-names-from-customers-on-the-app | shared | about the app: "How to Hide Vendor and Brand Names from Customers on the App" (in "Product Queries Step-by-step guides and how-tos for configuring, customizing, and managing all product-related features and settings across your app. ") |
| `vajro` | https://docs.vajro.com/en/articles/5106321-acquiring-your-storefront-access-token | shared | about the app: "Acquiring Your Storefront Access Token" (in "App Building 101 An in-depth glance at customizing and personalizing your mobile app with Vajro By Niwin 1 author") |
| `vajro` | https://docs.vajro.com/en/articles/7007893-what-is-the-mobile-app-sales-milestone | shared | about the app: "What is the mobile app sales milestone?" (what is) |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272571-white-label-branding | shared | about the app: "White Label Branding" (in "Features") |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272661-video-urls | shared | about the app: "Video URLs" (in "Features") |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272676-auto-submit-forms | shared | about the app: "Auto Submit Forms" (in "Features") |
| `virtue` | https://help.virtueimpact.com/en/articles/11652774-onboarding-for-ecommerce-donors-virtue-for-partners | shared | about the app: "Onboarding for eCommerce Donors - Virtue for Partners" (onboarding, names the app) |
| `virtue` | https://help.virtueimpact.com/en/articles/11660804-onboarding-for-smb-donors-virtue-for-partners | shared | about the app: "Onboarding for SMB Donors - Virtue for Partners" (onboarding, names the app) |
| `virtue` | https://help.virtueimpact.com/en/articles/8310622-dashboard-overview | shared | about the app: "Dashboard Overview" (overview, dashboard) |
| `weglot` | https://support.weglot.com/article/274-how-do-i-set-up-my-dns | shared | about the app: "How do I set up my DNS?" (in "Setup") |
| `weglot` | https://support.weglot.com/article/384-how-to-use-weglot-with-shopify-markets | shared | about the app: "How to use Weglot with Shopify Markets?" (in "Setup"; how to use, names the app) |
| `weglot` | https://support.weglot.com/article/408-how-to-switch-from-subdomains-to-subdirectories | shared | about the app: "How to switch from subdomains to subdirectories?" (in "Setup") |
| `yieldify` | http://support.yieldify.com/en/articles/10542287-feature-breakdown | shared | about the app: "Feature Breakdown Explore all the features Epsilon Accelerate has to offer." (in "Campaign Formats and Components All you need to know about campaign building By Sadhika and 3 others 4 authors"; features) |
| `yieldify` | http://support.yieldify.com/en/articles/13016967-epsilon-tag-features | shared | about the app: "Epsilon Tag Features Learn what features you unlock when you upgrade to the Epsilon tag." (in "Implementation Getting Started with Yieldify Technology By Sadhika and 1 other 2 authors"; features) |
| `yieldify` | http://support.yieldify.com/en/articles/5350250-campaign-scheduling | shared | about the app: "Campaign Scheduling Setting campaign start and end times" (in "Campaign Formats and Components All you need to know about campaign building By Sadhika and 3 others 4 authors") |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/10018448457498-Overview-of-Zendesk-AI-offerings | shared | about the app: "Overview of Zendesk AI offerings" (in "Getting started › Getting started with Zendesk Copilot"; overview, names the app) |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/5524125586330-About-Zendesk-Copilot | shared | about the app: "About Zendesk Copilot" (in "Getting started › Getting started with Zendesk Copilot"; about, names the app) |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/5608652527386-Getting-started-with-AI-features-in-the-Zendesk-Copilot-add-on | shared | about the app: "Getting started with AI features in the Zendesk Copilot add-on" (in "Getting started › Getting started with Zendesk Copilot"; getting started, features, names the app) |

## How each app overview was found

| integration | help centre | found via | method | picked |
|---|---|---|---|---:|
| `addglow` | — | — | — | 0 |
| `adobe_commerce_magento` | https://experienceleague.adobe.com/en/docs | guide | pages | 3 |
| `adroll` | — | — | — | 0 |
| `adscale` | https://help.adscale.com/en | catalog | — | 0 |
| `aftership` | https://support.aftership.com/en | probe | pages + sitemap | 3 |
| `aftership_personalization` | https://support.aftership.com/en | catalog | pages | 3 |
| `akeneo` | https://help.akeneo.com/ | catalog | pages + sitemap | 3 |
| `alloy_automation` | https://runalloy.com/ | homepage | pages + sitemap | 3 |
| `amasty` | https://amasty.com/docs | guide | — | 0 |
| `ampifyme` | https://help.ampifyme.com/ | probe | pages | 3 |
| `antavo` | https://antavo.atlassian.net/ | homepage | — | 0 |
| `appbrew` | — | — | — | 0 |
| `attentive` | https://help.attentivemobile.com/hc/en-us | catalog | zendesk-api | 3 |
| `bazaarvoice` | https://docs.bazaarvoice.com/home/en-us | override | pages | 3 |
| `beautytap` | — | — | — | 0 |
| `beeketing_boost_sales` | — | — | — | 0 |
| `bhn_rewards` | https://help.rybbon.net/hc/en-us | catalog | zendesk-api | 3 |
| `bigcommerce` | https://support.bigcommerce.com/ | guide | pages | 0 |
| `blueconic` | https://support-experiences.blueconic.com/en | catalog | pages | 3 |
| `bold_commerce` | https://support.boldcommerce.com/en | probe | pages | 0 |
| `boostcommerce` | https://support.boostcommerce.net/en | catalog | pages + llms.txt | 3 |
| `braze` | https://www.braze.com/docs | catalog | pages | 1 |
| `brevo_pushowl` | https://docs.pushowl.com/en | catalog | pages | 3 |
| `builder_io` | https://www.builder.io/ | homepage | pages | 2 |
| `checkout` | — | — | — | 0 |
| `checkout_plus` | — | — | — | 0 |
| `chimeable` | — | — | — | 0 |
| `cohley` | — | — | — | 0 |
| `cordial` | https://support.cordial.com/hc/en-us | guide | zendesk-api | 3 |
| `daasity` | https://help.daasity.com/ | catalog | pages | 3 |
| `daitafix` | https://daitafix.com/ | homepage | pages | 0 |
| `datagrail` | https://docs.datagrail.io/ | homepage | pages | 3 |
| `dialogue` | https://help.nowdialogue.com/en | catalog | pages | 0 |
| `digioh` | https://help.digioh.com/knowledgebase | catalog | — | 0 |
| `dixa` | https://support.dixa.help/en | catalog | pages + sitemap | 3 |
| `dondy` | https://help.dondy.net/ | probe | pages | 3 |
| `dotdigital` | https://marketing.help.dotdigital.com/en | catalog | pages | 3 |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en | catalog | pages | 3 |
| `drip` | https://www.drip.com/learn/docs | catalog | — | 0 |
| `ecocart` | https://support.ecocart.io/knowledge | homepage | — | 0 |
| `ecomposer` | https://help.ecomposer.io/docs | catalog | pages | 3 |
| `emarsys` | https://help.emarsys.com/hc/en-us | guide | zendesk-api | 0 |
| `expertvoice` | — | — | — | 0 |
| `facebook` | — | — | — | 0 |
| `fast_simon` | https://www.fastsimon.com/ | homepage | pages | 0 |
| `findify` | https://developers.findify.io/docs | catalog | pages | 0 |
| `flashchat` | — | — | — | 0 |
| `fobi` | — | — | — | 0 |
| `fomo` | https://fomo.family/ | homepage | pages | 0 |
| `fuego` | — | — | — | 0 |
| `fueled` | — | — | — | 0 |
| `gempages` | https://help.gempages.net/ | catalog | pages + sitemap | 3 |
| `gladly` | https://help.gladly.com/docs | catalog | pages | 3 |
| `glew` | https://www.glew.io/ | homepage | pages + sitemap | 3 |
| `gogenerosity` | https://help.gogenerosity.com/ | catalog | pages + sitemap | 3 |
| `google` | — | — | — | 0 |
| `gorgias` | https://docs.gorgias.com/en-US | guide | pages | 3 |
| `harbor` | — | — | — | 0 |
| `heartland_retail_by_hyperspace` | https://hyperspace.zendesk.com/hc/en-us | homepage | zendesk-api | 3 |
| `hubspot` | https://knowledge.hubspot.com/ | override | pages + sitemap | 3 |
| `insider` | https://academy.insiderone.com/docs | catalog | pages | 3 |
| `instagram` | — | — | — | 0 |
| `judge_me` | https://judge.me/help/en | catalog | pages | 0 |
| `kimonix` | http://help.kimonix.com/ | catalog | — | 0 |
| `klaviyo` | https://help.klaviyo.com/hc/en-us | guide | zendesk-api | 3 |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us | catalog | zendesk-api | 3 |
| `klevu` | https://help.klevu.com/support | catalog | zendesk-api | 3 |
| `knocommerce` | https://docs.knocommerce.com/en | catalog | pages | 3 |
| `later` | https://help.later.com/hc/en-us | homepage | zendesk-api | 3 |
| `lateshipment_com` | https://support.lateshipment.com/ | homepage | pages + sitemap | 3 |
| `lexer` | https://learn.lexer.io/docs | catalog | sitemap | 3 |
| `limespot` | https://support.limespot.com/en | catalog | pages | 3 |
| `listrak` | https://help.listrak.com/en | catalog | pages | 3 |
| `loop_subscriptions` | https://help.loopwork.co/en | catalog | pages + llms.txt | 3 |
| `loudcrowd` | https://help.loudcrowd.com/en | catalog | — | 0 |
| `loyaltylion` | https://help.loyaltylion.com/en | override | pages | 3 |
| `magenative` | https://www.magenative.com/ | homepage | pages | 0 |
| `mailchimp` | https://mailchimp.com/help | catalog | pages | 3 |
| `mesa` | https://docs.getmesa.com/ | catalog | pages + llms.txt | 3 |
| `movable_ink` | https://support.movableink.com/hc/en-us | guide | zendesk-api | 0 |
| `nosto` | https://help.nosto.com/en | homepage | pages | 3 |
| `novel` | https://support.novel.com/ | catalog | pages | 0 |
| `ometria` | https://support.ometria.com/hc/en-gb | catalog | zendesk-api | 3 |
| `omnisend` | https://support.omnisend.com/en | catalog | pages | 3 |
| `optimizely` | https://support.optimizely.com/ | homepage | zendesk-api + pages + sitemap | 3 |
| `optimove` | https://academy.optimove.com/en | catalog | — | 0 |
| `order_desk` | https://help.orderdesk.com/ | catalog | pages | 3 |
| `ordergroove` | https://docs.ordergroove.com/ | probe | pages + llms.txt | 3 |
| `pagefly` | https://help.pagefly.io/ | catalog | pages | 3 |
| `pie_eye` | — | — | — | 0 |
| `plobal_apps` | https://plobalapps.freshdesk.com/support | homepage | — | 0 |
| `poq` | — | — | — | 0 |
| `postpilot` | https://help.postpilot.com/knowledge | catalog | pages + sitemap | 3 |
| `postscript` | https://help.postscript.io/hc/en-us | guide | zendesk-api | 0 |
| `powerreviews` | https://www.powerreviews.com/ | probe | pages | 0 |
| `productsup` | https://www.productsup.com/ | homepage | pages + sitemap | 3 |
| `provesource` | — | — | — | 0 |
| `reactiv` | https://support.reactivapp.com/en | catalog | — | 0 |
| `reamaze` | https://support.reamaze.com/ | homepage | pages | 3 |
| `rebuy` | https://help.rebuyengine.com/en | catalog | pages + llms.txt | 3 |
| `recharge` | https://support.getrecharge.com/hc/en-us | guide | zendesk-api + sitemap | 3 |
| `refersion` | https://support.refersion.com/en | catalog | pages | 3 |
| `remarkety` | https://support.remarkety.com/hc/en-us | catalog | zendesk-api | 3 |
| `rep_ai` | — | — | — | 0 |
| `retention_science` | https://help.retentionscience.com/hc/en-us | guide | zendesk-api | 3 |
| `rise_ai` | https://help.rise.ai/en | catalog | llms.txt | 3 |
| `rule` | https://help.rule.io/sv | homepage | pages | 0 |
| `rush` | https://support.rush.app/ | catalog | pages | 3 |
| `sailthru` | — | — | — | 0 |
| `salesforce_commerce_cloud` | https://help.salesforce.com/ | probe | pages | 0 |
| `salesforce_marketing_cloud` | https://help.salesforce.com/ | guide | pages | 0 |
| `searchanise` | https://docs.searchanise.io/ | probe | pages | 3 |
| `searchspring` | https://help.searchspring.net/hc/en-us | catalog | zendesk-api | 3 |
| `shoelace` | — | — | — | 0 |
| `shogun` | https://getshogun.com/help/en | catalog | pages | 0 |
| `shopeaks` | — | — | — | 0 |
| `shopify` | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shopify_flow` | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shopify_plus` | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual | guide | pages | 3 |
| `shoppinggives` | https://faq.shoppinggives.com/hc/en-us | guide | zendesk-api | 0 |
| `siena` | https://support.siena.cx/hc/en-us | catalog | zendesk-api | 0 |
| `skeepers` | — | — | — | 0 |
| `smile_io` | https://help.smile.io/en | catalog | pages + llms.txt + sitemap | 1 |
| `social_nature` | https://socialnaturehelp.zendesk.com/ | homepage | zendesk-api | 3 |
| `sopost` | https://help.sopost.com/en | homepage | pages | 2 |
| `square_pos_by_defsys` | — | — | — | 0 |
| `stellar_reviews` | — | — | — | 0 |
| `stitch` | https://www.stitchdata.com/docs | catalog | pages | 3 |
| `subtotal` | https://subtotal.com/docs | catalog | pages | 3 |
| `swapt` | — | — | — | 0 |
| `syncly` | — | — | — | 0 |
| `talkable` | https://docs.talkable.com/ | catalog | pages | 3 |
| `tapcart` | https://help.tapcart.com/en | catalog | pages | 1 |
| `target` | — | — | — | 0 |
| `teamwork_commerce` | https://www.teamworkcommerce.com/ | homepage | pages | 0 |
| `tiktok_shop` | https://partner.tiktokshop.com/doc | guide | pages | 0 |
| `tray_io` | https://tray.ai/ | homepage | pages + sitemap | 1 |
| `treet` | https://treetbrandsuccess.zendesk.com/hc/en-us | catalog | zendesk-api + sitemap | 3 |
| `trend` | — | — | — | 0 |
| `triple_whale` | https://kb.triplewhale.com/en | catalog | llms.txt | 3 |
| `try_review` | — | — | — | 0 |
| `twitter` | — | — | — | 0 |
| `vajro` | https://docs.vajro.com/en | probe | pages + llms.txt | 3 |
| `viralsweep` | https://support.viralsweep.com/ | catalog | pages | 3 |
| `virtue` | https://help.virtueimpact.com/en | catalog | pages + llms.txt | 3 |
| `volusion` | — | — | — | 0 |
| `weglot` | https://support.weglot.com/ | guide | pages | 3 |
| `wonderment` | https://docs.wonderment.com/ | catalog | — | 0 |
| `woocommerce` | https://woocommerce.com/ | homepage | pages | 0 |
| `yieldify` | https://support.yieldify.com/en | probe | pages | 3 |
| `zembula` | — | — | — | 0 |
| `zendesk` | https://support.zendesk.com/hc/en-us | guide | zendesk-api | 3 |
| `zinrelo` | — | — | — | 0 |

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

### Help centre found, nothing picked (35)

- `adscale`: help centre https://help.adscale.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `amasty`: help centre https://amasty.com/docs found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `antavo`: help centre https://antavo.atlassian.net/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `bigcommerce`: help centre https://support.bigcommerce.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `bold_commerce`: help centre https://support.boldcommerce.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `daitafix`: help centre https://daitafix.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `dialogue`: help centre https://help.nowdialogue.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `digioh`: help centre https://help.digioh.com/knowledgebase found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `drip`: help centre https://www.drip.com/learn/docs found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `ecocart`: help centre https://support.ecocart.io/knowledge found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `emarsys`: help centre https://help.emarsys.com/hc/en-us found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `fast_simon`: help centre https://www.fastsimon.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `findify`: help centre https://developers.findify.io/docs found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `fomo`: help centre https://fomo.family/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `judge_me`: help centre https://judge.me/help/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `kimonix`: help centre http://help.kimonix.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `loudcrowd`: help centre https://help.loudcrowd.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `magenative`: help centre https://www.magenative.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `movable_ink`: help centre https://support.movableink.com/hc/en-us found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `novel`: help centre https://support.novel.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `optimove`: help centre https://academy.optimove.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `plobal_apps`: help centre https://plobalapps.freshdesk.com/support found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `postscript`: help centre https://help.postscript.io/hc/en-us found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `powerreviews`: help centre https://www.powerreviews.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `reactiv`: help centre https://support.reactivapp.com/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `rule`: help centre https://help.rule.io/sv found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `salesforce_commerce_cloud`: help centre https://help.salesforce.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `salesforce_marketing_cloud`: help centre https://help.salesforce.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `shogun`: help centre https://getshogun.com/help/en found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `shoppinggives`: help centre https://faq.shoppinggives.com/hc/en-us found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `siena`: help centre https://support.siena.cx/hc/en-us found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `teamwork_commerce`: help centre https://www.teamworkcommerce.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `tiktok_shop`: help centre https://partner.tiktokshop.com/doc found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `wonderment`: help centre https://docs.wonderment.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand
- `woocommerce`: help centre https://woocommerce.com/ found, but none of its pages, llms.txt or sitemap offered an overview-like article; pick some by hand

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

## Links proposed for two integrations (kept on the first) (12)

- https://help.klaviyo.com/hc/en-us/articles/15937542819355-Getting-started-with-Klaviyo-Reviews: `klaviyo`, also `klaviyo_customer_hub`
- https://help.shopify.com/en/manual/intro-to-shopify: `shopify`, also `shopify_flow`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup: `shopify`, also `shopify_flow`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/new-to-shopify-checklists/general-checklist: `shopify`, also `shopify_flow`
- https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/intro-to-shopify: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/new-to-shopify-checklists/general-checklist: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/intro-to-shopify: `shopify`, also `shopify_point_of_sale`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup: `shopify`, also `shopify_point_of_sale`
- https://help.shopify.com/en/manual/intro-to-shopify/initial-setup/new-to-shopify-checklists/general-checklist: `shopify`, also `shopify_point_of_sale`
- https://support.yotpo.com/docs/social-push: `facebook`, also `twitter`

## Already in the knowledge base (15)

- https://support.yotpo.com/docs/integrating-yotpo-reviews-with-attentive (in `attentive`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-attentive (in `attentive`)
- https://docs.pushowl.com/en/articles/14075206-yotpo-reviews-integration (in `brevo_pushowl`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital (in `dotdigital`)
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
