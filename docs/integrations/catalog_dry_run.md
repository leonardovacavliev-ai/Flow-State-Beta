<!-- Dry run of scripts/import_catalog.py, 2026-10-14, live catalog and partner sites; mechanics articles chosen by gemini-flash-latest from candidates the import found. The knowledge-base rows were a read-only copy of production (eval/seed_local_db.py). Nothing was written. -->

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
| proposals: partner mechanics articles (new) | 171 |
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

### Partner mechanics articles (171)

| integration | link | label | note |
|---|---|---|---|
| `aftership` | https://support.aftership.com/en/tracking/articles/15441384-frequently-asked-questions-about-shipment-tracking-and-statuses | shared | "Frequently asked questions about shipment tracking and statuses": Explains AfterShip's shipment tracking statuses and events that trigger post-purchase communications in Yotpo. |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322494-learn-about-different-product-recommendation-types | shared | "Learn About Different Product Recommendation Types Different Product Recommendation Types in AfterShip Personalization: follow setup steps, configure ": Explains the different product recommendation types and algorithms available in AfterShip Personalization where Yotpo star ratings will be displayed. |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322499-how-to-set-up-custom-recommendations-rules | shared | "How to Set up Custom Recommendations Rules Set up Custom Recommendations Rules in AfterShip Personalization: follow setup steps, configure key options": Explains how to configure custom recommendation rules to personalize product offerings across widgets. |
| `aftership_personalization` | https://support.aftership.com/en/personalization/articles/15322519-how-to-embed-smart-upsell-widgets-in-your-shopify-store-theme-2-0 | shared | "How to embed smart upsell widgets in your shopify store theme 2 0": Details how to embed and configure smart recommendation widgets on Shopify Theme 2.0 storefronts. |
| `akeneo` | https://help.akeneo.com/en_US/serenity-build-your-catalog/33-serenity-manage-your-product-identifiers | shared | "Serenity manage your product identifiers": Explains how product identifiers work in Akeneo, which is necessary for accurately matching products and SKUs with Yotpo. |
| `akeneo` | https://help.akeneo.com/en_US/serenity-build-your-catalog/serenity-manage-your-attributes | shared | "Manage your attributes": Explains how to set up and manage custom product attributes, which are used to store ratings and review metrics synced from Yotpo. |
| `akeneo` | https://help.akeneo.com/en_US/serenity-connect-your-pim/serenity-manage-your-connections | shared | "Manage your connections": Explains how to create and manage API connections in Akeneo to authorize data exchange with third-party apps like Yotpo. |
| `ampifyme` | https://help.ampifyme.com/article/119-can-i-have-reviews-on-my-amp-pages | shared | "Can i have reviews on my amp pages": Explains how customer review apps work and are supported on AmpifyMe's AMP pages. |
| `ampifyme` | https://help.ampifyme.com/article/19-how-to-display-amp-product-pages-instead-of-your-regular-ones | shared | "How to display amp product pages instead of your regular ones": Explains how to display AMP product pages to mobile shoppers, which is where the integrated Yotpo reviews appear. |
| `attentive` | https://help.attentive.com/hc/en-us/articles/360051937411-Create-a-dynamic-segment | shared | "Create a dynamic segment": Explains how to set up dynamic segments that automatically update based on subscriber criteria and synced review activity. |
| `attentive` | https://help.attentive.com/hc/en-us/articles/360056870971-Create-a-custom-journey | shared | "Create a custom journey": Explains how to build automated custom journeys triggered by specific events such as submitted or published reviews. |
| `attentive` | https://help.attentive.com/hc/en-us/articles/4409633925780-Personalize-Messages-with-Dynamic-Content | shared | "Personalize Messages with Dynamic Content": Explains how to insert dynamic subscriber and event data into message copy to personalize SMS and email campaigns. |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics/content-collection-partner | shared | "Partner Program": It explains the rules and standards Bazaarvoice requires when accepting syndicated content from third-party collection partners like Yotpo. |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/portal-basics/distribute-only | shared | "Distribute-only syndication": It explains how distribute-only syndication works for brands that collect content outside Bazaarvoice and syndicate it out to retail channels. |
| `bazaarvoice` | https://docs.bazaarvoice.com/articles/ratings-reviews/syndication | shared | "Syndication": It explains the core mechanisms, requirements, and matching processes Bazaarvoice uses to syndicate reviews and visual content across its retail network. |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/246905-form-screens-lead-capture-overview | shared | "Form screens (lead capture) overview": Explains how form screens capture contact information and zero-party subscriber data within interactive experiences. |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/704030-setup-launch-guide-personality-quiz-template | shared | "Setup & Launch Guide: Personality Quiz Template": Explains how to set up interactive personality quizzes that engage shoppers and collect zero-party preference data. |
| `blueconic` | https://support-experiences.blueconic.com/en/articles/724462-setup-launch-guide-lead-form-templates | shared | "Setup & Launch Guide: Lead Form Templates": Details how to configure and deploy lead form experiences designed to capture new subscribers. |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15848517-create-an-offer | shared | "Create an Offer": Explains the foundational process of defining trigger products and offer products in Bold Upsell where reviews will appear. |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15848518-create-an-upsell-offer | shared | "Create an Upsell Offer": Explains how to set up upgrade offers that prompt customers to replace a cart item with an upgraded product displaying Yotpo star ratings. |
| `bold_commerce` | https://support.boldcommerce.com/en/articles/15848520-create-a-cross-sell-offer | shared | "Create a Cross-sell Offer": Explains how to configure cross-sell offers that display additional recommended products featuring Yotpo review ratings. |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9360403-how-to-customize-the-display-of-your-search-results-pages | shared | "How to customize the display of your search results pages": Covers how to customize the layout and elements shown on search results pages where reviews and ratings appear. |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9393153-how-to-customize-the-product-item-section | shared | "How to customize the Product item section": Details how to configure the individual product item components, including review ratings, across search and collection views. |
| `boostcommerce` | https://support.boostcommerce.net/en/articles/9393177-how-to-customize-the-product-rating-element | shared | "How to customize the Product rating element": Explains how to display and customize the product rating and review count element on product cards. |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/10354875-custom-attributes-collect-and-use-third-party-data | shared | "Custom Attributes: Collect and Use Third-Party Data": Explains how to collect and use third-party custom attributes to personalize messaging with external data like loyalty points and tier status. |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/2317793-setting-up-automations | shared | "Setting up Automations": Explains how to set up automated messaging workflows triggered for subscribers. |
| `brevo_pushowl` | http://docs.pushowl.com/en/articles/4113148-segmentation-builder | shared | "Segmentation Builder Learn how to build an audience segment and the different conditions available to help you create highly specific segments.": Explains how to build customer segments using specific conditions and subscriber attributes to target loyalty audiences. |
| `cordial` | https://support.cordial.com/hc/en-us/articles/115005364367-Triggered-automated-messages | shared | "Triggered automated messages": Explains how to create automated messages triggered by events, which is how Yotpo's loyalty and referral event emails are sent from Cordial. |
| `cordial` | https://support.cordial.com/hc/en-us/articles/115005528368-Contact-attributes | shared | "Contact attributes": Explains how contact attributes are structured and stored in Cordial, which Yotpo populates with customer loyalty data like points balances and VIP tiers. |
| `cordial` | https://support.cordial.com/hc/en-us/articles/115005528508-Events | shared | "Events": Explains how custom events and event properties function in Cordial, which Yotpo creates to pass program actions like points earned and referral shares. |
| `daasity` | https://help.daasity.com/core-concepts/dashboards/creating-and-saving-custom-reports | shared | "Creating and Saving Custom Reports": Explains how to create and save custom reports and visualizations from the data available in Daasity. |
| `daasity` | https://help.daasity.com/core-concepts/data-models/data-explores | shared | "Start Exploring Data →": Explains how to use Daasity's Data Explores to query, filter, and analyze synced data such as customer reviews and orders. |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/access | shared | "Access Request Lifecycle": Explains the lifecycle and handling of data subject access requests when retrieving customer personal data from integrated platforms. |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/deletion | shared | "Deletion Request Lifecycle": Explains how DataGrail automates and processes data deletion requests across connected applications like Yotpo. |
| `datagrail` | https://docs.datagrail.io/docs/request-manager/settings/request-workflow-automation | shared | "Request Automations": Explains how to set up automated workflows to process privacy requests across connected integrations without manual intervention. |
| `dixa` | https://support.dixa.help/en/articles/2148-configurable-conversation-sidebar | shared | "Configurable conversation sidebar": Explains how to customize and arrange the conversation sidebar where integrated third-party customer data and cards are displayed to agents. |
| `dixa` | https://support.dixa.help/en/articles/53-customer-contact-info | shared | "Customer contact info": Explains how customer profile and contact details are viewed and managed by agents during conversations in Dixa. |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/create-pause-clone-or-delete-an-automation/8rDHseRyg4rfX9KinRBs2L | shared | "Create, pause, clone, or delete an automation": Explains how to manage, activate, pause, or clone WhatsApp automations used for messaging workflows. |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/create-your-first-whatsapp-automation/8rDHseRyg48xDwNqX73RF8 | shared | "Create your first WhatsApp automation": Explains how to set up and configure an automated WhatsApp message flow to message customers automatically. |
| `dondy` | https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/what-automations-can-you-build-with-dondy/8rDHseRyg1Pidpt8gA3kDo | shared | "What automations can you build with Dondy?": Explains the types of automated WhatsApp flows and triggers available within Dondy. |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198945-use-liquid-filters-to-display-contact-insight-data-information-in-a-email | shared | "Use liquid filters to display contact insight data information in a email": Explains how to use Liquid to dynamically display contact Insight data, such as synced review details or loyalty points, in email campaigns. |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8198962-working-with-the-program-builder | shared | "Working with the program builder": Explains how to build and configure automated multi-step customer programs and journeys triggered by customer engagement. |
| `dotdigital` | https://marketing.help.dotdigital.com/en/articles/8199282-use-insight-data-for-segmentation | shared | "Use Insight data for segmentation": Explains how to build customer segments using custom Insight data, which is how Yotpo reviews and loyalty records are stored in Dotdigital. |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/14110923-create-a-trigger-smartblock | shared | "Create a Trigger SmartBlock": It explains how to create dynamic Trigger SmartBlocks, which are the containers used to display personalized product recommendations and review data. |
| `dotdigital_personalization` | https://personalization.help.dotdigital.com/en/articles/8583713-add-star-ratings-to-cart-layouts-and-smartblocks | shared | "Add star ratings to cart layouts and SmartBlocks": It explains how to insert and style star ratings inside Dotdigital cart layouts and recommendation SmartBlocks. |
| `ecomposer` | https://help.ecomposer.io/docs/ecomposer-editor/section | shared | "Section Overview": Explains how to add, customize, and structure sections within the EComposer editor where widgets are placed. |
| `ecomposer` | https://help.ecomposer.io/docs/theme-sections | shared | "Theme Sections": Explains how to build standalone EComposer sections that can be inserted into existing store theme templates. |
| `gempages` | https://help.gempages.net/articles/add-product-reviews-star-ratings-to-your-product-page | shared | "Add product reviews star ratings to your product page": It explains how to add and position product review star rating elements within GemPages product layouts. |
| `gempages` | https://help.gempages.net/articles/introduction-to-library | shared | "Introduction to library": It explains how the GemPages Library works to search for, add, and manage third-party elements inside the page editor. |
| `gempages` | https://help.gempages.net/articles/understand-product-page-vs-product-template | shared | "Understand product page vs product template": It explains the distinction between individual product pages and product templates so merchants understand how widget placements apply across their catalog. |
| `gladly` | https://help.gladly.com/docs/customer-profile-and-my-customers-list-interface-overview | shared | "Customer Profile and My Customers List Interface Overview": Explains how the Customer Profile interface works in Gladly, where agents view unified customer context and integrated loyalty details. |
| `glew` | https://www.glew.io/articles/introducing-customer-export-and-advanced-filters-in-glew | shared | "Introducing customer export and advanced filters in glew": Explains how to apply advanced filters across customer datasets and export targeted segments in Glew. |
| `glew` | https://www.glew.io/articles/new-feature-customer-segments | shared | "New feature customer segments": Explains how customer segmentation works within Glew so merchants can build audiences based on imported customer and activity data. |
| `glew` | https://www.glew.io/guides/how-to-set-up-and-use-customer-segmentation-from-glew-in-mailchimp | shared | "How to set up and use customer segmentation from glew in mailchimp": Explains how to take Glew customer segments and push them to an email platform for targeted campaigns. |
| `gogenerosity` | https://help.gogenerosity.com/how-do-i-redeem-coupons-online | shared | "How do i redeem coupons online": It explains how shoppers redeem coupon codes online, which is relevant when loyalty points are converted into coupon rewards. |
| `gorgias` | https://docs.gorgias.com/en-US/connect-external-apps-to-gorgias-and-create-sidebar-widgets-81822 | shared | "Connect external apps to Gorgias and create sidebar widgets": Explains how sidebar widgets display data from connected apps alongside customer tickets in Gorgias. |
| `gorgias` | https://docs.gorgias.com/en-US/macro-variables-101-81845 | shared | "Use variables in macros": Explains how agents can populate macros with customer variables to quickly answer tickets with relevant profile data. |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/16135701518747-Adding-non-inventory-products-to-Heartland-Retail-Point-of-Sale | shared | "Adding non-inventory products to Heartland Retail Point of Sale": Explains how to create non-inventory items in Heartland Retail, which are commonly required to apply loyalty rewards and discounts at point of sale. |
| `heartland_retail_by_hyperspace` | https://support.hyperspacehq.com/hc/en-us/articles/360005491253-How-do-sales-sync-for-guest-customers | shared | "How do sales sync for guest customers?": Explains how Hyperspace handles transaction syncing for guest checkouts, which impacts customer tracking and points accrual. |
| `hubspot` | https://knowledge.hubspot.com/marketing-email/create-and-send-marketing-emails | shared | "Create and send marketing emails": It explains how to design and build marketing emails in HubSpot to send loyalty and referral updates to customers. |
| `insider` | https://academy.insiderone.com/docs/how-to-create-an-architect-journey | shared | "How to create an Architect journey": Explains how to set up automated omnichannel marketing journeys in Architect triggered by customer behavior and synced events. |
| `insider` | https://academy.insiderone.com/docs/personalize-emails-with-dynamic-content | shared | "Personalize emails with dynamic content": Explains how to personalize email marketing campaigns using dynamic customer attributes and data. |
| `insider` | https://academy.insiderone.com/docs/standard-segments-custom-attributes | shared | "Standard Segments: Custom Attributes": Explains how to build audience segments using custom user attributes such as loyalty tiers and point balances synced from Yotpo. |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/115000250912-Understanding-custom-profile-properties | shared | "Understanding custom profile properties": Explains how custom profile properties work in Klaviyo to store, view, and use synced loyalty data like points balances and tier status. |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/115002774952-Guide-to-Flow-Triggers-and-Flow-Filters | shared | "Guide to Flow Triggers and Flow Filters": Explains how Klaviyo flow triggers and filters operate, allowing merchants to target and restrict automated messages based on loyalty event data. |
| `klaviyo` | https://help.klaviyo.com/hc/en-us/articles/360003057151-How-to-create-a-metric-triggered-flow | shared | "How to create a metric-triggered flow": Explains how to set up automated flows triggered by incoming event metrics, such as customers earning points or redeeming rewards in Yotpo. |
| `klaviyo_customer_hub` | https://help.klaviyo.com/hc/en-us/articles/360003040052-How-to-create-a-segment-or-list-triggered-flow | shared | "How to create a segment- or list-triggered flow": segments and lists (the Yotpo guide or partner pages mention it) |
| `knocommerce` | https://docs.knocommerce.com/en/articles/5555408-creating-your-first-survey | shared | "Creating your First Survey": Explains how to build and configure a post-purchase survey in KnoCommerce where integration actions and rewards are triggered. |
| `knocommerce` | https://docs.knocommerce.com/en/articles/7885566-using-logic-in-surveys | shared | "Using Logic in Surveys": Explains how to set up conditional branching logic and completion paths within a survey. |
| `knocommerce` | https://docs.knocommerce.com/en/articles/9252329-targeting-audiences | shared | "Targeting Audiences": Explains how to define and segment which customer audiences are eligible to receive specific surveys. |
| `later` | https://help.later.com/hc/en-us/articles/360042743334-Collect-Media-from-Instagram-Posts-by-Hashtag | shared | "Collect Media from Instagram Posts by Hashtag": Explains how brands discover and collect influencer and customer posts across Instagram using specific campaign hashtags. |
| `later` | https://help.later.com/hc/en-us/articles/360042771474-Access-Organize-Your-Media-Library | shared | "Access & Organize Your Media Library": Explains how to organize, tag, and manage collected influencer and creator content within Later's media library. |
| `later` | https://help.later.com/hc/en-us/articles/360042771834-Collect-Media-from-Contributors | shared | "Collect Media from Contributors": Explains how brands collect original media and user-generated content directly from creators and contributors into Later. |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124130-how-can-i-send-or-automate-email-notifications-to-my-customers- | shared | "How can i send or automate email notifications to my customers": Details how to configure and automate customer email notifications based on shipping and delivery milestones. |
| `lateshipment_com` | https://support.lateshipment.com/support/solutions/articles/1070000124151-how-to-create-your-branded-tracking-page-in-your-lateshipment-com-account | shared | "How to create your branded tracking page in your lateshipment com account": Explains how to set up and customize the branded tracking page where post-purchase customer experience elements can be embedded. |
| `lexer` | https://learn.lexer.io/docs/lexers-attributes | shared | "Lexers attributes": Explains how customer attributes are structured and used across Lexer profiles and filters. |
| `lexer` | https://learn.lexer.io/docs/segment-activations | shared | "Segment activations": Explains how to activate customer segments to external channels for targeted campaigns and lookalike audiences. |
| `lexer` | https://learn.lexer.io/docs/segment-overview | shared | "Segment overview": Explains how to build and manage customer segments in Lexer using synced loyalty and review attributes. |
| `limespot` | https://support.limespot.com/en/articles/1443300-what-are-the-different-types-of-recommendation-boxes | shared | "What are the Different Types of Recommendation Boxes?": Explains the various types of recommendation boxes LimeSpot offers, which are the widgets where Yotpo ratings and reviews are displayed. |
| `limespot` | https://support.limespot.com/en/articles/1443304-how-to-add-remove-the-recommendation-boxes | shared | "How to Add/Remove the Recommendation Boxes": Explains how to add and manage recommendation boxes across store pages to showcase recommended products. |
| `limespot` | https://support.limespot.com/en/articles/3463292-customize-your-recommendation-boxes | shared | "Customize your recommendation boxes": Explains how to customize the design, settings, and layout of LimeSpot recommendation boxes on the storefront. |
| `listrak` | https://help.listrak.com/en/articles/5472394-custom-events-in-journey-hub | shared | "Custom Events in Journey Hub Learn how to trigger a journey based on an event you determine.": Explains how to create and use custom event triggers in Journey Hub, which is how Yotpo's loyalty and review events initiate automated workflows. |
| `listrak` | https://help.listrak.com/en/articles/9911144-using-handlebars-to-display-custom-event-data | shared | "Using Handlebars to Display Custom Event Data": Explains how to use Handlebars syntax to pull and display properties from custom event payloads directly inside message templates. |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12707618-customer-portal | shared | "Customer portal": Explains the setup and features of the subscriber customer portal where customers manage their upcoming orders and subscription details. |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12709682-apply-discounts | shared | "Apply discounts": Explains how discount codes can be applied directly to active subscriptions in the customer portal. |
| `loop_subscriptions` | https://help.loopwork.co/en/articles/12716873-subscription-discounts | shared | "Subscription discounts": Explains how discount codes and promotional rules are configured and handled for subscription orders in Loop. |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/1965582-what-are-activity-rules | shared | "What are activity rules How activity rules award points, and how to decide what a point is worth.": It explains how LoyaltyLion activity rules work, including setting point values and applying limits to customer actions. |
| `loyaltylion` | https://help.loyaltylion.com/en/articles/1965589-activity-leave-a-review | shared | "Activity: Leave a review Give points for reviews, whether your review platform has a dedicated rule or needs a custom one": It explains how to configure LoyaltyLion's review activity rule to reward customers with loyalty points when they leave a review. |
| `mailchimp` | https://mailchimp.com/help/all-the-starting-points | shared | "Marketing Automation Flow Triggers": Explains how starting points work to trigger automated customer journey flows when loyalty events occur. |
| `mailchimp` | https://mailchimp.com/help/create-and-send-to-a-segment | shared | "Guide to Creating and Sending to Segments in Mailchimp": Explains how to build and filter audience segments using synced loyalty fields like VIP tier and points balance. |
| `mailchimp` | https://mailchimp.com/help/getting-started-with-merge-tags | shared | "Getting Started with Merge Tags \| Mailchimp": Explains how to insert merge tags into campaigns to dynamically personalize messaging with customer loyalty attributes. |
| `mesa` | https://docs.getmesa.com/workflow-builder | shared | "Workflow Builder": Explains how to build and configure multi-step automations combining triggers and actions in MESA. |
| `mesa` | https://docs.getmesa.com/workflow-builder/actions | shared | "Actions": Explains how action steps work in MESA, which is how workflows update Yotpo or send Yotpo data to downstream systems. |
| `mesa` | https://docs.getmesa.com/workflow-builder/triggers | shared | "Triggers": Explains how triggers initiate MESA workflows, which is how Yotpo review and loyalty events kick off automations. |
| `nosto` | https://help.nosto.com/en/articles/1453130-how-to-use-user-generated-content-ugc-in-recommendations | shared | "How to use User-Generated Content (UGC) in Recommendations?": Explains how to incorporate and display visual user-generated content within on-site product recommendation widgets. |
| `nosto` | https://help.nosto.com/en/articles/586919-adding-product-review-ratings-to-your-recommendation-templates | shared | "Adding product review ratings to your Recommendation templates": Explains how to enable and display product review ratings and review counts inside Nosto's recommendation templates. |
| `nosto` | https://help.nosto.com/en/articles/9519472-how-to-add-ugc-as-an-hover-effect-to-product-recommendations | shared | "How to add UGC as an Hover Effect to Product Recommendations": Explains how to configure recommendation widgets to display user-generated content photos as a hover effect on recommended products. |
| `novel` | https://support.novel.com/start-guide/create-your-pass | shared | "Create your pass": Explains how to set up and configure the mobile wallet pass that displays customer loyalty points and tier information. |
| `novel` | https://support.novel.com/start-guide/customer-tags | shared | "Customer Tags": Explains how Novel applies tags to customer profiles when passes are installed, which ties into loyalty attribution. |
| `novel` | https://support.novel.com/start-guide/distribute-your-pass | shared | "Distribute your pass": Explains how to distribute wallet passes through QR codes and links so in-store customers can install them. |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/4407949072273-Create-a-custom-field | shared | "Create a custom field": Explains how to set up contact and product custom fields in Ometria to receive and store synced Yotpo loyalty data. |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/9882372857757-Managing-custom-fields | shared | "Managing custom fields": Explains how to manage, edit, and configure custom field settings across contact records. |
| `ometria` | https://support.ometria.com/hc/en-gb/articles/9882443672861-Testing-your-custom-fields | shared | "Testing your custom fields": Explains how to test and verify that custom field values populate properly for contacts before launching personalized campaigns. |
| `omnisend` | https://support.omnisend.com/en/articles/1061885-collect-manage-contact-custom-properties | shared | "Collect & Manage Contact Custom Properties": It explains how contact custom properties are stored and managed, which is where Yotpo syncs loyalty and review attributes. |
| `omnisend` | https://support.omnisend.com/en/articles/3947985-understand-omnisend-automation-trigger-settings | shared | "Understand Omnisend Automation Trigger Settings": It explains how automation triggers work so you can launch workflows from Yotpo custom loyalty and review events. |
| `omnisend` | https://support.omnisend.com/en/articles/4298431-understand-event-data-in-automation-workflows | shared | "Understand Event Data in Automation Workflows": It explains how to access and use the specific data payload passed by custom event triggers inside automation workflows. |
| `order_desk` | https://help.orderdesk.com/guided-walkthroughs/orders-and-folders/how-to-begin-importing-orders | shared | "How to Begin Importing Orders": Explains how to import orders from various sales channels and shopping carts into Order Desk so they can be forwarded to Yotpo. |
| `order_desk` | https://help.orderdesk.com/guided-walkthroughs/rules-and-automations/how-to-create-your-first-automation | shared | "How to create Your First Automation": Explains how to build automated rules in Order Desk to route and process orders based on specific conditions. |
| `order_desk` | https://help.orderdesk.com/resources/rules-reference-events-filters-and-actions | shared | "Rules Reference: Events, Filters and Actions": Provides a comprehensive reference of rule events, filters, and actions for automating when and how orders are submitted to integrations. |
| `ordergroove` | https://docs.ordergroove.com/lifecycle/order/recurring-placement | shared | "Recurring Order Placement": Explains how Ordergroove schedules and places recurring subscription orders with your eCommerce platform, which is what triggers recurring Yotpo loyalty points and order tags. |
| `ordergroove` | https://docs.ordergroove.com/lifecycle/sm/customer-overview | shared | "Subscription Manager From The Customer's Perspective": Explains the subscriber interface where customers manage upcoming recurring orders and apply discount codes or rewards. |
| `ordergroove` | https://docs.ordergroove.com/lifecycle/sm/external-apis | shared | "Integrating External APIs in the Subscription Manager": Explains how to connect third-party APIs into the Subscription Manager, which is relevant for surfacing loyalty point balances and redemption options. |
| `pagefly` | https://help.pagefly.io/page-structure-and-elements/shopify-elements/custom-content/how-to-use-shopify-app-block-element-with-pagefly-section | shared | "App blocks": Explains how to add and configure Shopify app block elements within PageFly sections to embed third-party app widgets. |
| `pagefly` | https://help.pagefly.io/pages-and-sections-creation/pages/add-more-content-to-my-shopify-product-page | shared | "How to create a Product page with PageFly": Explains how to build and customize product pages in PageFly where product review, star rating, and Q&A widgets are typically placed. |
| `postpilot` | https://help.postpilot.com/knowledge/flow-triggers | shared | "Flow triggers": Explains how flow triggers work in PostPilot to automatically initiate direct mail sends based on customer actions and criteria. |
| `postpilot` | https://help.postpilot.com/knowledge/how-do-i-add-a-coupon-to-my-campaign | shared | "How do i add a coupon to my campaign": Explains how to attach dynamic or static coupon codes to direct mail cards to deliver loyalty rewards and incentives. |
| `postpilot` | https://help.postpilot.com/knowledge/whats-the-difference-between-automated-and-one-off-campaigns | shared | "Whats the difference between automated and one off campaigns": Explains the difference between one-off drops and automated campaigns that send direct mail dynamically on an ongoing basis. |
| `reamaze` | https://support.reamaze.com/kb/about-your-customers/customer-data-attributes | shared | "Customer Profiles & Data Attributes": Explains how Re:amaze manages customer profiles and data attributes that store external information like Yotpo loyalty and reviews data. |
| `reamaze` | https://support.reamaze.com/kb/automation/setting-up-automation-workflows | shared | "Setting up automation workflows": Explains how to set up automated workflows to tag and manage conversations based on customer conditions and attributes. |
| `reamaze` | https://support.reamaze.com/kb/learning-re-amaze/responding-to-and-managing-conversations | shared | "The Conversation View: Layout and Features": Explains the conversation interface where customer details and third-party integration data are displayed alongside support tickets. |
| `rebuy` | https://help.rebuyengine.com/en/articles/6526958-how-to-target-specific-customer-segments-using-customer-tag-rules | shared | "How to Target Specific Customer Segments Using Customer Tag Rules": It explains how to create data source rules based on customer tags to personalize widget offers for specific segments like VIP tiers. |
| `rebuy` | https://help.rebuyengine.com/en/articles/6593888-smart-cart-apps | shared | "Smart Cart™ Apps Learn how to integrate third-party apps with Rebuy's Smart Cart to enhance your store's functionality.​": It explains how third-party app integrations are enabled, configured, and positioned inside Rebuy's Smart Cart. |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360008683234-Applying-and-removing-a-discount-from-an-existing-subscription | shared | "Applying and removing a discount from an existing subscription": It covers how discounts can be applied directly to active, recurring subscriptions by customers or merchants. |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360008829873-Using-Shopify-order-and-customer-tags | shared | "Using Shopify order and customer tags": It details the automated customer and order tags Recharge generates in Shopify, which are used to trigger Yotpo earning rules for subscription events. |
| `recharge` | https://support.getrecharge.com/hc/en-us/articles/360034748173-Managing-subscription-discount-codes | shared | "Managing subscription discount codes": It explains how subscription discount codes behave in Recharge and how customers can apply them within their account. |
| `refersion` | http://support.refersion.com/en/articles/1906618-how-do-i-automatically-approve-affiliate-applications | shared | "How Do I Automatically Approve Affiliate Applications?": Explains how to automatically approve affiliate applications, which directly determines whether Yotpo awards loyalty points instantly upon registration or after manual review. |
| `refersion` | http://support.refersion.com/en/articles/2952798-customize-promote-your-affiliate-registration-page | shared | "Customize & Promote Your Affiliate Registration Page": Explains how to locate, configure, and customize the affiliate registration page that customers are directed to from the Yotpo Custom Action campaign. |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/208149026-How-does-the-abandoned-cart-campaign-work | shared | "How does the "abandoned cart" campaign work?": Explains the triggers and configuration for abandoned cart campaigns, which is a key automated email flow used to showcase Yotpo review social proof. |
| `remarkety` | https://support.remarkety.com/hc/en-us/articles/360035250851-How-to-easily-use-products-from-your-catalog-in-an-email-Product-Row-Builder | shared | "How to easily use products from your catalog in an email - Product Row Builder": Explains how to add and format dynamic product blocks in email templates using the Product Row Builder, where synced product review data is displayed. |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/115003287847-Advanced-merge-tags-and-conditional-statements | shared | "Advanced merge tags and conditional statements": Explains how to use conditional statements with merge tags to dynamically show or hide email content based on customer property values. |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/215162088-Merge-tag-overview-All-available-tags-and-how-to-use-them | shared | "Merge tag overview: All available tags and how to use them": Explains how to insert and use merge tags in Retention Science emails to display synced customer data like loyalty points and referral links. |
| `retention_science` | https://help.retentionscience.com/hc/en-us/articles/221502408-How-to-build-a-new-segment-to-target-certain-customers | shared | "How to build a new segment to target certain customers": Explains how to create customer segments in Retention Science to target audiences based on customer attributes. |
| `rise_ai` | http://help.rise.ai/en/articles/3115295-how-customers-redeem-store-credit | shared | "How Customers Redeem Store Credit": Explains how shoppers access and apply their earned store credit rewards during checkout. |
| `rise_ai` | http://help.rise.ai/en/articles/4002309-how-to-set-up-your-store-credit-and-gift-card-emails | shared | "How to Set Up Your Store Credit and Gift Card Emails": Explains how to configure and brand the email notifications that deliver reward gift cards and store credit to customers. |
| `rise_ai` | http://help.rise.ai/en/articles/4002969-create-store-credit-loyalty-workflows | shared | "Create Store Credit & Loyalty Workflows": Explains how to set up automated loyalty and store credit workflows in Rise.ai to reward customer actions. |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/201184839-Setting-Up-Custom-Sort-on-a-Filter | shared | "Setting Up Custom Sort on a Filter": Explains how to customize the display order of filter facet values, such as ordering rating filters from highest to lowest. |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/203776879-4-Managing-Field-Settings | shared | "4. Managing Field Settings": Explains how to configure product field settings in Searchspring to enable attributes like review scores for faceting, sorting, and display. |
| `searchspring` | https://help.searchspring.net/hc/en-us/articles/206986683-Sort-Options | shared | "Sort Options": Explains how to create and configure sort options for shoppers on search and category pages, such as sorting items by rating. |
| `shopify` | https://help.shopify.com/en/manual/customers/customer-accounts/customize-customer-accounts | shared | "Customize customer accounts": Explains how to customize Shopify's customer accounts and embed app extensions directly into the customer portal. |
| `shopify` | https://help.shopify.com/en/manual/customers/customer-accounts/new-customer-accounts | shared | "Customer accounts": Explains how to set up customer accounts and configure login settings between classic and new customer accounts, which Yotpo Loyalty requires for shoppers to access their rewards. |
| `shopify` | https://help.shopify.com/en/manual/discounts/discount-methods/discount-codes | shared | "Discount codes": Explains how discount codes are structured and applied in Shopify, which is the underlying mechanism used when customers redeem loyalty points for rewards. |
| `shopify_plus` | https://help.shopify.com/en/manual/online-store/themes/customizing-themes/theme-editor | shared | "Theme editor": Explains how to use the Shopify theme editor to enable app embeds, which is necessary for Yotpo on-site widgets to display. |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/sell-in-person/getting-started/smart-grid | shared | "Smart grid": Explains how to customize the Shopify POS smart grid and add app tiles, which is where the Yotpo POS UI extension is installed and accessed. |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/sell-in-person/shopify-pos/customer-management/add-customer-profile-to-cart | shared | "Add customer profile to cart": Explains how staff attach a customer profile to an in-store cart, which is required to associate purchases with loyalty members and redeem rewards. |
| `shopify_point_of_sale` | https://help.shopify.com/en/manual/sell-in-person/shopify-pos/customer-management/create-customer-profile | shared | "Create customer profile": Explains how to create a new customer profile in POS during checkout to capture email addresses and enroll shoppers into the loyalty program. |
| `smile_io` | https://help.smile.io/en/articles/4036265-earning-rules-ways-customers-can-earn-points | shared | "Earning rules: Ways customers can earn points": Explains the foundational earning rule mechanics and how Smile.io calculates and awards points to participating customers. |
| `smile_io` | https://help.smile.io/en/articles/4036267-configure-ways-to-earn-points | shared | "Configure ways to earn points": Explains how to set up and manage ways for customers to earn points in Smile.io, which is where review-based rewards are configured. |
| `smile_io` | https://help.smile.io/en/articles/4036269-configure-points-earning-limits | shared | "Configure points earning limits": Explains how to restrict how often customers can earn points for completing an action, which helps prevent points abuse when rewarding reviews. |
| `stitch` | https://www.stitchdata.com/docs/replication/replication-scheduling/replication-frequency | shared | "Replication Frequency": Explains how to configure how frequently Stitch extracts and replicates data from integrations like Yotpo to your data warehouse. |
| `stitch` | https://www.stitchdata.com/docs/replication/syncing-historical-saas-data-resetting-replication-keys | shared | "Historical SaaS data": Explains how to replicate historical data or re-sync past records from SaaS sources like Yotpo by resetting replication keys. |
| `stitch` | https://www.stitchdata.com/docs/replication/syncing-new-additional-columns | shared | "Replicating new and additional columns": Explains how to select and replicate new or additional fields and columns from a connected data source into your destination. |
| `subtotal` | https://subtotal.com/docs/guides/ios-subtotal-link | shared | "Link accounts in your iOS App": Explains how to implement Subtotal's account linking workflow within a mobile app so shoppers can connect their retailer and brand accounts. |
| `talkable` | https://docs.talkable.com/advanced_features/personal_coupon_sharing | shared | "Advocate Personal Coupon Sharing": Explains how advocate personal coupon codes are configured, distributed, and tracked to attribute referrals. |
| `talkable` | https://docs.talkable.com/advanced_features/referrals_approval | shared | "Referrals Approval": Explains the criteria and workflow for approving pending referrals before rewards and loyalty incentives are issued. |
| `talkable` | https://docs.talkable.com/wallet.md | shared | "What the pass carries": Explains the dynamic customer and reward data stored and displayed on Talkable's mobile wallet passes. |
| `triple_whale` | https://kb.triplewhale.com/en/articles/5960333-understanding-and-utilizing-attribution-models | shared | "Understanding and Utilizing Attribution Models": Explains how Triple Whale's attribution models track and weigh customer touchpoints across the buyer journey. |
| `triple_whale` | https://kb.triplewhale.com/en/articles/6355008-creating-custom-metrics | shared | "Creating Custom Metrics": Explains how to build custom metrics and calculations using data pulled from integrated tools. |
| `triple_whale` | https://kb.triplewhale.com/en/articles/9653103-create-a-custom-dashboard | shared | "Create a Custom Dashboard": Explains how to build custom dashboards and widgets to monitor and report on integrated data. |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272637-expand-social-actions | shared | "Expand Social Actions": Explains how to display social actions expanded by default so participants immediately see entry opportunities like leaving a product review. |
| `viralsweep` | https://support.viralsweep.com/en/articles/9272775-social-actions | shared | "Social Actions": Explains how social actions work in ViralSweep promotions and how participants earn bonus entries for completing designated actions. |
| `virtue` | https://help.virtueimpact.com/en/articles/8263362-setting-up-giving-campaigns | shared | "Setting up giving campaigns": Explains how to create and configure giving campaigns in Virtue, establishing how donations and causes are tracked across the store. |
| `virtue` | https://help.virtueimpact.com/en/articles/8263516-how-to-find-causes | shared | "How to find causes": Explains how to search and select from Virtue's catalog of partner charities to feature in loyalty donation options. |
| `virtue` | https://help.virtueimpact.com/en/articles/8264178-how-do-causes-receive-funds | shared | "How do causes receive funds?": Explains how funds generated from customer interactions and redemptions are disbursed and delivered to the chosen charities. |
| `weglot` | https://support.weglot.com/article/253-how-to-translate-dynamic-content | shared | "How to translate dynamic content?": It explains how to ensure dynamically generated JavaScript content is detected and translated, which is essential for client-rendered Yotpo reviews, galleries, and loyalty widgets. |
| `weglot` | https://support.weglot.com/article/302-how-can-i-add-variables-to-my-translations | shared | "How can i add variables to my translations": It explains how to set up dynamic variables in translations so values like points balances and customer names in loyalty modules are preserved across languages. |
| `weglot` | https://support.weglot.com/article/95-how-to-exclude-urls-blocks-words-from-translation | shared | "How can I exclude URLs, blocks, or words from translation?": It explains how to exclude specific CSS blocks or words from translation, allowing merchants to prevent translation of brand names, customer handles, or loyalty discount codes. |
| `yieldify` | http://support.yieldify.com/en/articles/11478574-dynamic-content | shared | "Dynamic Content How to create highly targeted and relevant on-site experiences that speak directly to each visitor.": Explains how to display personalized, dynamic on-site content tailored to specific visitor data and customer segments. |
| `yieldify` | http://support.yieldify.com/en/articles/5162502-coupon-code | shared | "Coupon Code Understanding the static and dynamic coupon code components": Explains how to implement static and dynamic coupon components to distribute discount and reward codes to shoppers. |
| `yieldify` | http://support.yieldify.com/en/articles/5162515-dynamic-social-proof | shared | "Dynamic Social Proof Understanding the dynamic social proof component": Explains how to set up the dynamic social proof component used to showcase customer ratings and reviews directly on-site. |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/4408829476378-Setting-up-multiple-brands | shared | "Setting up multiple brands": It explains how Zendesk Multibrand and brand-specific routing operate, which is necessary for connecting multiple Yotpo stores to distinct Zendesk brands. |
| `zendesk` | https://support.zendesk.com/hc/en-us/articles/8263915942938-About-the-ticket-lifecycle-and-ticket-statuses | shared | "About the ticket lifecycle and ticket statuses": It explains the ticket lifecycle and the Solved status condition that triggers Yotpo's post-service review request emails. |

Mechanics articles were chosen by `gemini-flash-latest` from candidates the import found (200 calls, 214,968 input and 11,123 output tokens, 2 failed and fell back to topic scoring).

## How each integration's mechanics articles were found

Topics: what was searched for, best first (ranked by what the Yotpo guide and partner pages talk about; the lists are in `backend/mechanics_topics.py`).

| integration | topics searched | help centre | found via | method | picked |
|---|---|---|---|---|---:|
| `addglow` | points and rewards; importing customers and balances; referrals and VIP tiers | — | — | — | 0 |
| `adobe_commerce_magento` | "order statuses and states"; "managing store views"; "add widget product page" | https://experienceleague.adobe.com/en/docs | guide | pages + llms.txt + ai | 0 |
| `adroll` | product feeds; campaigns; personalisation in messages | — | — | — | 0 |
| `adscale` | "create ad strategy"; "social proof ads"; "audience targeting" | https://help.adscale.com/en | catalog | ai | 0 |
| `aftership` | "shipment tracking statuses"; "tracking event webhooks"; "automated delivery notifications" | https://support.aftership.com/en | probe | pages + llms.txt + sitemap + ai | 1 |
| `aftership_personalization` | "product recommendation widget"; "display review ratings"; "recommendation widget settings" | https://support.aftership.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `akeneo` | "ratings and reviews"; "manage product attributes"; "enrich products" | https://help.akeneo.com/ | catalog | pages + sitemap + ai | 3 |
| `alloy_automation` | "building workflows"; "triggers and actions"; "workflow recipes" | https://runalloy.com/ | homepage | sitemap + ai | 0 |
| `amasty` | "Improved Sorting configuration"; "Improved Sorting options"; "sort by rating" | https://amasty.com/docs | guide | ai | 0 |
| `ampifyme` | "product page reviews"; "product details settings"; "reviews rich snippets" | https://help.ampifyme.com/ | probe | pages + sitemap + ai | 2 |
| `antavo` | "gamified reviews module"; "reward points rules"; "create rewards" | https://antavo.atlassian.net/ | homepage | ai | 0 |
| `appbrew` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `attentive` | "create dynamic segments"; "create a journey"; "custom journey triggers" | https://help.attentivemobile.com/hc/en-us | catalog | zendesk-search + ai | 3 |
| `bazaarvoice` | "inbound review syndication"; "Bazaarvoice network syndication"; "visual content syndication" | https://docs.bazaarvoice.com/home/en-us | override | pages + ai | 3 |
| `beautytap` | campaigns; product catalog and feeds; content, rights and galleries | — | — | — | 0 |
| `beeketing_boost_sales` | widgets and templates; targeting and display rules; custom data and code | — | — | — | 0 |
| `bhn_rewards` | "create reward campaign"; "reward approval queue"; "campaign test mode" | https://help.rybbon.net/hc/en-us | catalog | zendesk-search + sitemap + ai | 0 |
| `bigcommerce` | "using Script Manager"; "managing product reviews"; "product review emails" | https://support.bigcommerce.com/ | guide | ai | 0 |
| `blueconic` | "create quiz experience"; "profile properties data collection"; "lead capture forms" | https://support-experiences.blueconic.com/en | catalog | pages + ai | 3 |
| `bold_commerce` | "create upsell offer"; "upsell offer display settings"; "product upsell popup settings" | https://support.boldcommerce.com/en | probe | pages + ai | 3 |
| `boostcommerce` | "filter by rating"; "show product rating"; "customize product card" | https://support.boostcommerce.net/en | catalog | llms.txt + sitemap + ai | 3 |
| `braze` | "Connected Content"; "Personalization with Liquid"; "create email campaign" | https://www.braze.com/docs | catalog | pages + ai | 0 |
| `brevo_pushowl` | "marketing automation workflow triggers"; "dynamic contact attributes"; "create contact segments" | https://docs.pushowl.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `builder_io` | "register custom components"; "visual editor custom blocks"; "installing plugins" | https://www.builder.io/ | homepage | pages + sitemap + ai | 0 |
| `checkout` | checkout; discount codes; customer accounts | — | — | — | 0 |
| `checkout_plus` | checkout; discount codes; customer accounts | — | — | — | 0 |
| `chimeable` | content, rights and galleries; review collection and requests; campaigns | — | — | — | 0 |
| `cohley` | content, rights and galleries; creators and affiliates; campaigns | — | — | — | 0 |
| `cordial` | "event triggered message automation"; "use event data messages"; "contact attributes" | https://support.cordial.com/hc/en-us | guide | zendesk-search + sitemap + ai | 3 |
| `daasity` | "customer segmentation"; "pre-built dashboards"; "data warehouse models" | https://help.daasity.com/ | catalog | pages + llms.txt + sitemap + ai | 2 |
| `daitafix` | "sentiment analysis"; "automated customer engagement"; "customer review analytics" | https://daitafix.com/ | homepage | ai | 0 |
| `datagrail` | "Request Manager DSR workflow"; "continuous system detection"; "consent and preference management" | https://docs.datagrail.io/ | homepage | pages + llms.txt + sitemap + ai | 3 |
| `dialogue` | "product recommendations"; "audience segmentation"; "content widgets" | https://help.nowdialogue.com/en | catalog | ai | 0 |
| `digioh` | "product recommendation quiz"; "dynamic product recommendations"; "quiz completion redirect" | https://help.digioh.com/knowledgebase | catalog | ai | 0 |
| `dixa` | "custom cards"; "conversation sidebar cards"; "customer activity timeline" | https://support.dixa.help/en | catalog | sitemap + ai | 2 |
| `dondy` | "Shopify Flow automation"; "WhatsApp review requests"; "WhatsApp discount codes" | https://help.dondy.net/ | probe | pages + llms.txt + sitemap + ai | 3 |
| `dotdigital` | "program builder"; "create a segment"; "insight data" | https://marketing.help.dotdigital.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `dotdigital_personalization` | "product recommendations"; "email product recommendations"; "display ratings in recommendations" | https://personalization.help.dotdigital.com/en | catalog | pages + llms.txt + sitemap + ai | 2 |
| `drip` | "create a workflow"; "create customer segments"; "custom event properties" | https://www.drip.com/learn/docs | catalog | ai | 0 |
| `ecocart` | "carbon neutral order product"; "cart offset widget"; "ecommerce product setup" | https://support.ecocart.io/knowledge | homepage | ai | 0 |
| `ecomposer` | "third party extensions"; "add extension element"; "extension library" | https://help.ecomposer.io/docs | catalog | pages + ai | 2 |
| `emarsys` | "external events"; "automation center external event"; "custom contact fields" | https://help.emarsys.com/hc/en-us | guide | ai | 0 |
| `expertvoice` | product catalog and feeds; review collection and requests; campaigns | — | — | — | 0 |
| `facebook` | content, rights and galleries; product feeds; audiences | — | — | — | 0 |
| `fast_simon` | "filter by rating"; "sort search results"; "instant search display" | https://www.fastsimon.com/ | homepage | ai | 0 |
| `findify` | "filter by rating"; "display star ratings"; "product card customization" | https://developers.findify.io/docs | catalog | ai | 0 |
| `flashchat` | segments and lists; flows and their triggers; delays, filters and re-entry | — | — | — | 0 |
| `fobi` | customers at the point of sale; passes and their fields; discounts at the point of sale | — | — | — | 0 |
| `fomo` | "customize notification template"; "notification display settings"; "filter notifications" | https://fomo.family/ | homepage | ai | 0 |
| `fuego` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `fueled` | workflows: triggers and actions; data sync and connectors; dashboards and reports | — | — | — | 0 |
| `gempages` | "third party elements library"; "add elements to page"; "product page builder" | https://help.gempages.net/ | catalog | pages + sitemap + ai | 3 |
| `gladly` | "App Platform"; "Customer Profile cards"; "Customer Profile overview" | https://help.gladly.com/docs | catalog | pages + llms.txt + ai | 1 |
| `glew` | "create customer segments"; "push customer segments"; "build custom reports" | https://www.glew.io/ | homepage | pages + sitemap + ai | 3 |
| `gogenerosity` | "donate loyalty points"; "donation rewards setup"; "redeem points donation" | https://help.gogenerosity.com/ | catalog | pages + sitemap + ai | 1 |
| `google` | product catalog and feeds; product feeds; review collection and requests | — | — | — | 0 |
| `gorgias` | "customer sidebar widgets"; "customize customer sidebar"; "responding to tickets" | https://docs.gorgias.com/en-US | guide | pages + llms.txt + sitemap + ai | 2 |
| `harbor` | points and rewards; importing customers and balances; referrals and VIP tiers | — | — | — | 0 |
| `heartland_retail_by_hyperspace` | "add customer to sale"; "apply coupon point of sale"; "promotions and discounts" | https://hyperspace.zendesk.com/hc/en-us | homepage | zendesk-search + ai | 2 |
| `hubspot` | "set workflow enrollment triggers"; "create and edit properties"; "send automated emails workflows" | https://knowledge.hubspot.com/ | override | pages + sitemap + ai | 1 |
| `insider` | "custom events and attributes"; "Architect journey triggers"; "create dynamic segments" | https://academy.insiderone.com/docs | catalog | pages + llms.txt + ai | 3 |
| `instagram` | content, rights and galleries; audiences; product feeds | — | — | — | 0 |
| `judge_me` | "reward conditions"; "reward reviewers with coupons"; "rewards settings" | https://judge.me/help/en | catalog | pages + ai | 0 |
| `kimonix` | "collection sorting strategies"; "personalized product recommendations"; "email product recommendations" | http://help.kimonix.com/ | catalog | ai | 0 |
| `klaviyo` | "metric triggered flow"; "segment by profile properties"; "custom profile properties" | https://help.klaviyo.com/hc/en-us | guide | zendesk-search + ai | 3 |
| `klaviyo_customer_hub` | "Customer Hub extensions"; "Customer Hub loyalty"; "Customize Customer Hub" | https://help.klaviyo.com/hc/en-us | catalog | zendesk-search + rules (the model failed) | 3 |
| `klevu` | "display ratings search results"; "filter by rating facets"; "merchandising rules rating" | https://help.klevu.com/support | catalog | ai | 0 |
| `knocommerce` | "post purchase surveys"; "survey rewards"; "survey builder" | https://docs.knocommerce.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `later` | "content library management"; "product sampling campaigns"; "influencer content rights" | https://help.later.com/hc/en-us | homepage | zendesk-search + sitemap + ai | 3 |
| `lateshipment_com` | "branded tracking page"; "delivery notifications"; "delivery feedback" | https://support.lateshipment.com/ | homepage | pages + sitemap + ai | 2 |
| `lexer` | "segment builder"; "customer attributes"; "activate audiences" | https://learn.lexer.io/docs | catalog | sitemap + ai | 3 |
| `limespot` | "recommendation boxes"; "recommendation box designer"; "display product ratings" | https://support.limespot.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `listrak` | flows and their triggers; segments and lists; custom properties and events | https://help.listrak.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `loop_subscriptions` | "apply discount customer portal"; "subscription discount codes"; "discounts upcoming orders" | https://help.loopwork.co/en | catalog | llms.txt + sitemap + ai | 3 |
| `loudcrowd` | "social rewards"; "reward rules"; "Instagram UGC tracking" | https://help.loudcrowd.com/en | catalog | ai | 0 |
| `loyaltylion` | "reward points for reviews"; "reviews activity rule"; "custom activity rules" | https://help.loyaltylion.com/en | override | pages + llms.txt + sitemap + ai | 2 |
| `magenative` | "loyalty points"; "product reviews widget"; "customer rewards" | https://www.magenative.com/ | homepage | ai | 0 |
| `mailchimp` | "customer journey starting points"; "create an audience segment"; "getting started with merge tags" | https://mailchimp.com/help | catalog | pages + llms.txt + sitemap + ai | 3 |
| `mesa` | "workflow triggers"; "workflow actions"; "workflow builder steps" | https://docs.getmesa.com/ | catalog | pages + llms.txt + sitemap + ai | 3 |
| `movable_ink` | "API data source"; "Studio data sources"; "dynamic creative editor" | https://support.movableink.com/hc/en-us | guide | ai | 0 |
| `nosto` | "product recommendations review ratings"; "recommendation template customization"; "on-site pop-up campaigns" | https://help.nosto.com/en | homepage | pages + llms.txt + sitemap + ai | 3 |
| `novel` | "wallet pass push notifications"; "POS pass redemption"; "loyalty wallet pass setup" | https://support.novel.com/ | catalog | pages + llms.txt + sitemap + ai | 3 |
| `ometria` | "create custom fields"; "segment contacts custom fields"; "personalising email campaigns" | https://support.ometria.com/hc/en-gb | catalog | zendesk-search + sitemap + ai | 3 |
| `omnisend` | "automation workflow triggers"; "segmentation custom properties"; "custom event automation" | https://support.omnisend.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `optimizely` | "customer predictions"; "create customer segments"; "custom fields attributes" | https://support.optimizely.com/hc/en-us | homepage | zendesk-search + pages + sitemap + ai | 0 |
| `optimove` | "real-time campaigns"; "creating target groups"; "managing custom events" | https://academy.optimove.com/en | catalog | ai | 0 |
| `order_desk` | "Rule Builder"; "Rule Builder actions"; "Managing orders" | https://help.orderdesk.com/ | catalog | pages + llms.txt + sitemap + ai | 3 |
| `ordergroove` | "apply coupon to subscription"; "recurring order discounts"; "shopify order tags" | https://docs.ordergroove.com/ | probe | pages + llms.txt + sitemap + ai | 3 |
| `pagefly` | "third party elements"; "product reviews element"; "add app widgets" | https://help.pagefly.io/ | catalog | pages + llms.txt + sitemap + ai | 2 |
| `pie_eye` | data subject requests | — | — | — | 0 |
| `plobal_apps` | "product page reviews"; "loyalty rewards redeem"; "discount code checkout" | https://plobalapps.freshdesk.com/support | homepage | ai | 0 |
| `poq` | blocks and components; product pages; customer accounts and login | — | — | — | 0 |
| `postpilot` | "automated campaigns"; "campaign triggers"; "audience segmentation" | https://help.postpilot.com/knowledge | catalog | pages + sitemap + ai | 3 |
| `postscript` | "flow builder triggers"; "create subscriber segment"; "subscriber custom properties" | https://help.postscript.io/hc/en-us | guide | ai | 0 |
| `powerreviews` | "retail syndication network"; "brand review syndication"; "syndication product matching" | https://www.powerreviews.com/ | probe | ai | 0 |
| `productsup` | "add export destination"; "set up exports"; "schedule exports" | https://www.productsup.com/ | homepage | sitemap + ai | 0 |
| `provesource` | widgets and templates; targeting and display rules; custom data and code | — | — | — | 0 |
| `reactiv` | "Reactiv Clips"; "product page reviews"; "loyalty points and rewards" | https://support.reactivapp.com/en | catalog | ai | 0 |
| `reamaze` | "customer data panel"; "tagging conversations"; "workflow automation rules" | https://support.reamaze.com/ | homepage | pages + sitemap + ai | 3 |
| `rebuy` | "Smart Cart apps"; "data source customer tags"; "widget product reviews" | https://help.rebuyengine.com/en | catalog | pages + llms.txt + sitemap + ai | 2 |
| `recharge` | "subscription discount codes"; "order and customer tags"; "shopify flow triggers" | https://support.getrecharge.com/hc/en-us | guide | zendesk-search + sitemap + ai | 3 |
| `refersion` | "affiliate registration page"; "approve affiliate applications"; "affiliate sign up settings" | https://support.refersion.com/en | catalog | pages + llms.txt + sitemap + ai | 2 |
| `remarkety` | "product reviews email template"; "abandoned cart automation"; "browse abandonment campaign" | https://support.remarkety.com/hc/en-us | catalog | zendesk-search + sitemap + ai | 2 |
| `rep_ai` | customer profile in the sidebar; macros and replies; rules and automations | — | — | — | 0 |
| `retention_science` | "custom merge tags"; "custom customer attributes"; "segment custom attributes" | https://help.retentionscience.com/hc/en-us | guide | zendesk-search + sitemap + ai | 3 |
| `rise_ai` | "issue store credit"; "reward workflows"; "gift card rewards" | https://help.rise.ai/en | catalog | llms.txt + ai | 3 |
| `rule` | "create custom fields"; "marketing automation triggers"; "create dynamic segments" | https://help.rule.io/sv | homepage | pages + llms.txt + sitemap + ai | 0 |
| `rush` | "shipment delivery status"; "tracking events triggers"; "delivery notification events" | https://support.rush.app/ | catalog | pages + ai | 0 |
| `sailthru` | flows and their triggers; custom properties and events; segments and lists | — | — | — | 0 |
| `salesforce_commerce_cloud` | "cartridge path Business Manager"; "custom site preferences"; "Page Designer custom components" | https://help.salesforce.com/ | probe | ai | 0 |
| `salesforce_marketing_cloud` | "link data extension Contact Builder"; "Contact Builder Data Designer"; "Journey Builder entry source" | https://help.salesforce.com/ | guide | ai | 0 |
| `searchanise` | "instant search widget"; "search results page"; "product ratings" | https://docs.searchanise.io/ | probe | pages + sitemap + ai | 0 |
| `searchspring` | "managing facets"; "product badges"; "sort options" | https://help.searchspring.net/hc/en-us | catalog | zendesk-search + sitemap + ai | 3 |
| `shoelace` | results, badges and merchandising; filters and facets; recommendation widgets | — | — | — | 0 |
| `shogun` | "product review element"; "product box element"; "custom html element" | https://getshogun.com/help/en | catalog | ai | 0 |
| `shopeaks` | product feeds; audiences; campaigns | — | — | — | 0 |
| `shopify` | "theme app embeds"; "set up customer accounts"; "new customer accounts" | https://help.shopify.com/en/manual | guide | pages + sitemap + ai | 3 |
| `shopify_flow` | "creating workflows"; "workflow triggers and actions"; "using template variables" | https://help.shopify.com/en/manual | guide | pages + sitemap + ai | 0 |
| `shopify_plus` | "app embeds theme editor"; "setting up customer accounts"; "new customer accounts" | https://help.shopify.com/en/manual | guide | pages + sitemap + ai | 3 |
| `shopify_point_of_sale` | "customize POS smart grid"; "apps in Shopify POS"; "apply discounts Shopify POS" | https://help.shopify.com/en/manual | guide | pages + sitemap + ai | 3 |
| `shoppinggives` | "redeem points for donation"; "create donation campaign"; "loyalty points donation" | https://faq.shoppinggives.com/hc/en-us | guide | ai | 0 |
| `siena` | "automated responses"; "customer context variables"; "AI actions" | https://support.siena.cx/hc/en-us | catalog | ai | 0 |
| `skeepers` | campaigns; content, rights and galleries; creators and affiliates | — | — | — | 0 |
| `smile_io` | "ways to earn points"; "points for reviews"; "manage earning rules" | https://help.smile.io/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `social_nature` | "syndicate reviews"; "product sampling reviews"; "sampling campaign disclaimer" | https://socialnaturehelp.zendesk.com/hc/en-us | homepage | zendesk-search + pages + sitemap + ai | 0 |
| `sopost` | "collect ratings and reviews"; "post trial survey"; "review syndication" | https://help.sopost.com/en | homepage | pages + ai | 0 |
| `square_pos_by_defsys` | discounts at the point of sale; customers at the point of sale; apps on the point of sale | — | — | — | 0 |
| `stellar_reviews` | review collection and requests; campaigns; product catalog and feeds | — | — | — | 0 |
| `stitch` | "replication methods"; "replication frequency settings"; "table column selection" | https://www.stitchdata.com/docs | catalog | pages + ai | 3 |
| `subtotal` | "account linking"; "shopper identification"; "POS data sharing" | https://subtotal.com/docs | catalog | pages + ai | 1 |
| `swapt` | customers at the point of sale; discounts at the point of sale; apps on the point of sale | — | — | — | 0 |
| `syncly` | workflows: triggers and actions; data sync and connectors; dashboards and reports | — | — | — | 0 |
| `talkable` | "reward webhooks"; "custom rewards"; "advocate reward rules" | https://docs.talkable.com/ | catalog | pages + llms.txt + sitemap + ai | 3 |
| `tapcart` | "App Studio blocks"; "product detail page layout"; "customer account screen" | https://help.tapcart.com/en | catalog | pages + ai | 0 |
| `target` | product catalog and feeds; content, rights and galleries; review collection and requests | — | — | — | 0 |
| `teamwork_commerce` | "loyalty rewards POS register"; "redeem customer rewards checkout"; "customer loyalty points balance" | https://www.teamworkcommerce.com/ | homepage | ai | 0 |
| `tiktok_shop` | "import product reviews"; "product rating seller center"; "product identifier code" | https://partner.tiktokshop.com/doc | guide | ai | 0 |
| `tray_io` | "building workflows"; "webhook trigger"; "connector authentication" | https://tray.ai/ | homepage | llms.txt + sitemap + ai | 0 |
| `treet` | "seller payout options"; "seller brand credit"; "issuing seller credit" | https://treetbrandsuccess.zendesk.com/hc/en-us | catalog | zendesk-search + sitemap + ai | 0 |
| `trend` | content, rights and galleries; campaigns; creators and affiliates | — | — | — | 0 |
| `triple_whale` | "customer journey touchpoints"; "attribution models"; "summary dashboard metrics" | https://kb.triplewhale.com/en | catalog | llms.txt + ai | 3 |
| `try_review` | content, rights and galleries; review collection and requests; campaigns | — | — | — | 0 |
| `twitter` | product catalog and feeds; content, rights and galleries; review collection and requests | — | — | — | 0 |
| `vajro` | "product reviews"; "product detail page"; "reviews and ratings" | https://docs.vajro.com/en | probe | pages + llms.txt + sitemap + ai | 0 |
| `viralsweep` | "social actions"; "award bonus entries"; "sweepstakes campaign setup" | https://support.viralsweep.com/ | catalog | llms.txt + sitemap + ai | 2 |
| `virtue` | "choose causes"; "create giving campaign"; "points donation" | https://help.virtueimpact.com/en | catalog | pages + llms.txt + sitemap + ai | 3 |
| `volusion` | apps in the theme; discount codes; customer accounts | — | — | — | 0 |
| `weglot` | "translate dynamic content"; "translate iframe"; "customize language switcher" | https://support.weglot.com/ | guide | pages + sitemap + ai | 3 |
| `wonderment` | "custom tracking URL"; "estimated delivery date"; "shipping event properties" | https://docs.wonderment.com/ | catalog | ai | 0 |
| `woocommerce` | "enable product reviews"; "managing order statuses"; "managing product reviews" | https://woocommerce.com/ | homepage | ai | 0 |
| `yieldify` | "dynamic content"; "campaign formats"; "audience targeting" | https://support.yieldify.com/en | probe | pages + ai | 3 |
| `zembula` | personalisation in messages; workflows: triggers and actions; data sync and connectors | — | — | — | 0 |
| `zendesk` | "understanding ticket statuses"; "setting up multibrand"; "finding zendesk subdomain" | https://support.zendesk.com/hc/en-us | guide | zendesk-search + ai | 2 |
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

### Help centre found, nothing picked (50)

- `adobe_commerce_magento`: help centre https://experienceleague.adobe.com/en/docs found; the model judged none of its 2 candidates good enough; pick some by hand
- `adscale`: help centre https://help.adscale.com/en found, but no article on "create ad strategy", "social proof ads", "audience targeting"; pick some by hand
- `alloy_automation`: help centre https://runalloy.com/ found; the model judged none of its 5 candidates good enough; pick some by hand
- `amasty`: help centre https://amasty.com/docs found, but no article on "Improved Sorting configuration", "Improved Sorting options", "sort by rating"; pick some by hand
- `antavo`: help centre https://antavo.atlassian.net/ found, but no article on "gamified reviews module", "reward points rules", "create rewards"; pick some by hand
- `bhn_rewards`: help centre https://help.rybbon.net/hc/en-us found; the model judged none of its 13 candidates good enough; pick some by hand
- `bigcommerce`: help centre https://support.bigcommerce.com/ found, but no article on "using Script Manager", "managing product reviews", "product review emails"; pick some by hand
- `braze`: help centre https://www.braze.com/docs found; the model judged none of its 3 candidates good enough; pick some by hand
- `builder_io`: help centre https://www.builder.io/ found, but no article on "register custom components", "visual editor custom blocks", "installing plugins"; pick some by hand
- `daitafix`: help centre https://daitafix.com/ found, but no article on "sentiment analysis", "automated customer engagement", "customer review analytics"; pick some by hand
- `dialogue`: help centre https://help.nowdialogue.com/en found, but no article on "product recommendations", "audience segmentation", "content widgets"; pick some by hand
- `digioh`: help centre https://help.digioh.com/knowledgebase found, but no article on "product recommendation quiz", "dynamic product recommendations", "quiz completion redirect"; pick some by hand
- `drip`: help centre https://www.drip.com/learn/docs found, but no article on "create a workflow", "create customer segments", "custom event properties"; pick some by hand
- `ecocart`: help centre https://support.ecocart.io/knowledge found, but no article on "carbon neutral order product", "cart offset widget", "ecommerce product setup"; pick some by hand
- `emarsys`: help centre https://help.emarsys.com/hc/en-us found, but no article on "external events", "automation center external event", "custom contact fields"; pick some by hand
- `fast_simon`: help centre https://www.fastsimon.com/ found, but no article on "filter by rating", "sort search results", "instant search display"; pick some by hand
- `findify`: help centre https://developers.findify.io/docs found, but no article on "filter by rating", "display star ratings", "product card customization"; pick some by hand
- `fomo`: help centre https://fomo.family/ found, but no article on "customize notification template", "notification display settings", "filter notifications"; pick some by hand
- `judge_me`: help centre https://judge.me/help/en found, but no article on "reward conditions", "reward reviewers with coupons", "rewards settings"; pick some by hand
- `kimonix`: help centre http://help.kimonix.com/ found, but no article on "collection sorting strategies", "personalized product recommendations", "email product recommendations"; pick some by hand
- `klevu`: help centre https://help.klevu.com/support found, but no article on "display ratings search results", "filter by rating facets", "merchandising rules rating"; pick some by hand
- `loudcrowd`: help centre https://help.loudcrowd.com/en found, but no article on "social rewards", "reward rules", "Instagram UGC tracking"; pick some by hand
- `magenative`: help centre https://www.magenative.com/ found, but no article on "loyalty points", "product reviews widget", "customer rewards"; pick some by hand
- `movable_ink`: help centre https://support.movableink.com/hc/en-us found, but no article on "API data source", "Studio data sources", "dynamic creative editor"; pick some by hand
- `optimizely`: help centre https://support.optimizely.com/hc/en-us found; the model judged none of its 30 candidates good enough; pick some by hand
- `optimove`: help centre https://academy.optimove.com/en found, but no article on "real-time campaigns", "creating target groups", "managing custom events"; pick some by hand
- `plobal_apps`: help centre https://plobalapps.freshdesk.com/support found, but no article on "product page reviews", "loyalty rewards redeem", "discount code checkout"; pick some by hand
- `postscript`: help centre https://help.postscript.io/hc/en-us found, but no article on "flow builder triggers", "create subscriber segment", "subscriber custom properties"; pick some by hand
- `powerreviews`: help centre https://www.powerreviews.com/ found, but no article on "retail syndication network", "brand review syndication", "syndication product matching"; pick some by hand
- `productsup`: help centre https://www.productsup.com/ found; the model judged none of its 1 candidates good enough; pick some by hand
- `reactiv`: help centre https://support.reactivapp.com/en found, but no article on "Reactiv Clips", "product page reviews", "loyalty points and rewards"; pick some by hand
- `rule`: help centre https://help.rule.io/sv found; the model judged none of its 13 candidates good enough; pick some by hand
- `rush`: help centre https://support.rush.app/ found; the model judged none of its 1 candidates good enough; pick some by hand
- `salesforce_commerce_cloud`: help centre https://help.salesforce.com/ found, but no article on "cartridge path Business Manager", "custom site preferences", "Page Designer custom components"; pick some by hand
- `salesforce_marketing_cloud`: help centre https://help.salesforce.com/ found, but no article on "link data extension Contact Builder", "Contact Builder Data Designer", "Journey Builder entry source"; pick some by hand
- `searchanise`: help centre https://docs.searchanise.io/ found; the model judged none of its 30 candidates good enough; pick some by hand
- `shogun`: help centre https://getshogun.com/help/en found, but no article on "product review element", "product box element", "custom html element"; pick some by hand
- `shopify_flow`: help centre https://help.shopify.com/en/manual found; the model judged none of its 30 candidates good enough; pick some by hand
- `shoppinggives`: help centre https://faq.shoppinggives.com/hc/en-us found, but no article on "redeem points for donation", "create donation campaign", "loyalty points donation"; pick some by hand
- `siena`: help centre https://support.siena.cx/hc/en-us found, but no article on "automated responses", "customer context variables", "AI actions"; pick some by hand
- `social_nature`: help centre https://socialnaturehelp.zendesk.com/hc/en-us found; the model judged none of its 10 candidates good enough; pick some by hand
- `sopost`: help centre https://help.sopost.com/en found; the model judged none of its 1 candidates good enough; pick some by hand
- `tapcart`: help centre https://help.tapcart.com/en found; the model judged none of its 2 candidates good enough; pick some by hand
- `teamwork_commerce`: help centre https://www.teamworkcommerce.com/ found, but no article on "loyalty rewards POS register", "redeem customer rewards checkout", "customer loyalty points balance"; pick some by hand
- `tiktok_shop`: help centre https://partner.tiktokshop.com/doc found, but no article on "import product reviews", "product rating seller center", "product identifier code"; pick some by hand
- `tray_io`: help centre https://tray.ai/ found; the model judged none of its 4 candidates good enough; pick some by hand
- `treet`: help centre https://treetbrandsuccess.zendesk.com/hc/en-us found; the model judged none of its 3 candidates good enough; pick some by hand
- `vajro`: help centre https://docs.vajro.com/en found; the model judged none of its 22 candidates good enough; pick some by hand
- `wonderment`: help centre https://docs.wonderment.com/ found, but no article on "custom tracking URL", "estimated delivery date", "shipping event properties"; pick some by hand
- `woocommerce`: help centre https://woocommerce.com/ found, but no article on "enable product reviews", "managing order statuses", "managing product reviews"; pick some by hand

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

## Links proposed for two integrations (kept on the first) (6)

- https://help.klaviyo.com/hc/en-us/articles/115002774952-Guide-to-Flow-Triggers-and-Flow-Filters: `klaviyo`, also `klaviyo_customer_hub`
- https://help.klaviyo.com/hc/en-us/articles/360003057151-How-to-create-a-metric-triggered-flow: `klaviyo`, also `klaviyo_customer_hub`
- https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/customers/customer-accounts/new-customer-accounts: `shopify`, also `shopify_plus`
- https://help.shopify.com/en/manual/discounts/discount-methods/discount-codes: `shopify`, also `shopify_plus`
- https://support.yotpo.com/docs/social-push: `facebook`, also `twitter`

## Already in the knowledge base (16)

- https://support.yotpo.com/docs/integrating-yotpo-reviews-with-attentive (in `attentive`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-attentive (in `attentive`)
- https://docs.pushowl.com/en/articles/14075206-yotpo-reviews-integration (in `brevo_pushowl`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital (in `dotdigital`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-emarsys (in `emarsys`)
- https://support.yotpo.com/docs/klaviyo-oauth-integration-yotpo-loyalty-referrals (in `klaviyo`)
- https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo (in `klaviyo`)
- https://support.yotpo.com/docs/klaviyo-integration-guide (in `klaviyo`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak (in `listrak`)
- https://help.listrak.com/en/articles/6909272-loyalty-automations-in-listrak-conductor (in `listrak`)
- https://support.yotpo.com/docs/ometria-integration-guide-for-loyalty-referrals (in `ometria`)
- https://support.yotpo.com/docs/ometria-integration-guide-for-reviews (in `ometria`)
- https://support.ometria.com/hc/en-gb/articles/4800701859997-Setting-up-Yotpo-Loyalty-Referrals (in `ometria`)
- https://support.yotpo.com/docs/omnisend-integration-guide-for-yotpo-loyalty-referrals (in `omnisend`)
- https://support.yotpo.com/docs/postscript-integration-guide-for-yotpo-loyalty-referrals (in `postscript`)
- https://support.yotpo.com/docs/creating-loyalty-referrals-workflows-in-shopify-flow (in `global`)
