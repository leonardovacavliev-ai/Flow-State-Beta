<!-- Dry run of scripts/import_catalog.py, 2026-10-14, live catalog and partner sites. Partner mechanics: gemini-flash-latest listed the functions from each integration's own documents and accepted articles after reading them; a person approves each final list. The knowledge-base rows were a read-only copy of production (eval/seed_local_db.py). Nothing was written. -->

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
| proposals: partner mechanics articles (new) | 268 |
| help centres that could not be read automatically (a person picks) | 39 |
| guides gone (404, no renamed match) | 1 |
| detail pages with nothing documentary | 13 |
| integrations with no help centre found | 37 |
| links already in the knowledge base (skipped) | 17 |
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

## Partner mechanics, per integration

The model (`gemini-flash-latest`, 256 calls, 981,929 input and 56,155 output tokens, 0 failed) read what Yotpo and the partner wrote about each integration, listed the partner functions it touches, and accepted only articles whose text explains one. A person approves each integration's final list in the admin.

### `adobe_commerce_magento`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/adobe-commerce-2-setting-up-yotpo-reviews-extension-245-330, Adobe Commerce (Magento) page about Yotpo https://marketplace.magento.com/yotpo-magento2-module-yotpo-loyalty.html, Adobe Commerce (Magento) page about Yotpo https://commercemarketplace.adobe.com/yotpo-module-yotpo.html. Help centre: https://experienceleague.adobe.com/en/docs (pages + llms.txt); 14 articles read.

Functions:
- **Order Statuses**: Order status updates in Adobe Commerce (such as Complete, Processing, or Pending) trigger order syncs to Yotpo for automated review requests and loyalty point earning.
- **Store Views**: Allows configuration settings, credentials, and order sync rules to be scoped and applied independently to specific storefronts in multi-store Adobe Commerce setups.
- **Theme Templates and Blocks**: Merchants edit product and category page template files (.phtml) to place PHP helper code that renders reviews widgets and star ratings.
- **Template Path Hints**: Used by merchants as a diagnostic tool to locate the exact template and block files within their theme when positioning Yotpo code snippets.
- **Checkout**: Adobe Commerce's checkout flow serves as a surface for loyalty reward redemption at checkout and displaying UGC content.

Accepted: none. the model accepted none of the 14 articles it read

### `aftership`

Read: Yotpo catalog card, AfterShip Tracking help centre: Set up yotpo integration, AfterShip Tracking help centre: Connect yotpo sms with aftership tracking, AfterShip Tracking help centre: Connect yotpo reviews with aftership tracking. Help centre: https://support.aftership.com/en (pages + llms.txt + sitemap); 19 articles read.

Functions:
- **Shipment tracking statuses and events**: AfterShip Tracking detects delivery checkpoints (such as Delivered, In transit, Out for delivery, and Exception) and sends these event updates to trigger review request emails and SMS flows in Yotpo.
- **SMS notification settings**: Merchants configure and disable AfterShip Tracking's native SMS notifications to prevent duplicate text messages when sending status alerts via Yotpo SMS.
- **Shipment tracking fields and properties**: AfterShip Tracking exports shipment attributes (such as courier slug, tracking number, title, substatus message, and pickup location) to populate dynamic variables in Yotpo messages.
- **Branded tracking page**: AfterShip Tracking generates tracking page URLs pointing to the merchant's branded tracking page, which are exported to Yotpo for inclusion in post-purchase communications.
- **Estimated delivery date (EDD)**: AfterShip calculates or captures carrier and AI-based estimated delivery dates and shares the EDD data with Yotpo to inform customers in SMS notifications.

Accepted:
- [Learn about shipment tracking using a test slug and number](https://support.aftership.com/en/tracking/articles/15441358-learn-about-shipment-tracking-using-a-test-slug-and-number) (Shipment tracking statuses and events): This article defines the primary shipment status codes and sub-status codes used to monitor delivery checkpoints throughout the tracking lifecycle.
- [How to enable ai predictive post purchase estimated delivery dates](https://support.aftership.com/en/tracking/articles/15441628-how-to-enable-ai-predictive-post-purchase-estimated-delivery-dates) (Estimated delivery date (EDD)): This article explains how to enable and set up AI predictive post-purchase estimated delivery dates for shipments.
- [Learn about post purchase estimated delivery dates edds](https://support.aftership.com/en/tracking/articles/15441631-learn-about-post-purchase-estimated-delivery-dates-edds) (Estimated delivery date (EDD)): This article explains how post-purchase estimated delivery dates are determined, prioritized, and displayed across tracking touchpoints.
- [Enable and disable shipping notifications](https://support.aftership.com/en/tracking/articles/15441683-enable-and-disable-shipping-notifications) (SMS notification settings): This article explains how to navigate to shipment notification settings and toggle email and SMS notification triggers on or off.

### `aftership_personalization`

Read: Yotpo catalog card, AfterShip Personalization page about Yotpo https://support-personalization.automizely.com/en/article/set-up-yotpo-integration-1p1o97i, AfterShip Personalization help centre: Set up yotpo integration, AfterShip Personalization help centre: Connect yotpo sms with aftership tracking, AfterShip Personalization help centre: Connect yotpo reviews with aftership tracking. Help centre: https://support.aftership.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Product recommendations**: Displays Yotpo star ratings and review counts directly on recommended products to build trust and boost conversions.
- **Pre-purchase and post-purchase scenarios**: Merchants enable Yotpo product reviews within pre-purchase or post-purchase recommendation scenarios.
- **Personalized product offers**: Uses synchronized Yotpo review data to automatically personalize product offerings and maximize recommendation relevancy.
- **Store connections**: Configures which connected store syncs customer and review data into AfterShip Personalization.

Accepted:
- [Connect Shopify With AfterShip Personalization Connect your Shopify store to AfterShip Personalization in a few clicks to launch personalized upsell a](https://support.aftership.com/en/personalization/articles/15322477-connect-shopify-with-aftership-personalization) (Store connections): This article explains how to connect a Shopify store to AfterShip Personalization to enable product recommendations and upsell campaigns.
- [Learn About Different Product Recommendation Types Different Product Recommendation Types in AfterShip Personalization: follow setup steps, configure](https://support.aftership.com/en/personalization/articles/15322494-learn-about-different-product-recommendation-types) (Product recommendations): This article explains the different recommendation algorithms and types available in AfterShip Personalization to generate product suggestions.
- [How to Set Up Cart Popup Product Recommendations Set Up Cart Popup Product Recommendations in AfterShip Personalization: follow setup steps, configure](https://support.aftership.com/en/personalization/articles/15322488-how-to-set-up-cart-popup-product-recommendations) (Pre-purchase and post-purchase scenarios): This article explains how to set up and configure cart popup product recommendation widgets for pre-purchase upselling.
- [Set Up Post-purchase Upsell Offers Set Up Post-purchase Upsell Offers in AfterShip Personalization: follow setup steps, configure key options, verify](https://support.aftership.com/en/personalization/articles/15322516-set-up-post-purchase-upsell-offers) (Pre-purchase and post-purchase scenarios): This article explains how to create and customize post-purchase upsell offers displayed to customers immediately after completing a purchase.

### `akeneo`

Read: Yotpo catalog card, Akeneo page about Yotpo https://help.akeneo.com/rating-reviews/rating-reviews-with-yotpo, Akeneo help centre: Rating reviews with yotpo. Help centre: https://help.akeneo.com/ (pages + sitemap); 20 articles read.

Functions:
- **PX Insights (Rating & Reviews)**: Displays Yotpo ratings, review signals, and aggregated customer review data directly on product records in the PIM.
- **Connected Apps**: Manages the connection, store configurations, and multi-store authentication between Akeneo and Yotpo.
- **Web API Permissions**: Controls user access levels required within Akeneo to view and interact with synchronized review data.
- **Synchronization Status and Reporting**: Provides sync logs and error reports to troubleshoot failed product reconciliations or missing common identifiers.

Accepted:
- [Serenity manage your apps](https://help.akeneo.com/en_US/v7-connect-your-pim/serenity-manage-your-apps) (Connected Apps): Explains how to access and manage installed apps in the Connected Apps menu and configure user role permissions required to open their interfaces.
- [Serenity manage the web api permissions](https://help.akeneo.com/en_US/serenity-permissions/47-serenity-manage-the-web-api-permissions) (Web API Permissions): Explains how to configure role-based permissions and endpoint access levels for Web API connection users.
- [Serenity how to connect my pim with apps](https://help.akeneo.com/en_US/serenity-connect-your-pim/serenity-how-to-connect-my-pim-with-apps) (Connected Apps): Explains the process of connecting third-party apps from the App Store and granting required catalog permissions through the authorization wizard.
- [Visualize rating and reviews insights and take actions](https://help.akeneo.com/en_US/px-insights-ratings-reviews/visualize-rating-and-reviews-insights-and-take-actions) (PX Insights (Rating & Reviews)): Explains how to add rating and review count columns to the Product Grid and visualize customer review data on product records.
- [Rating reviews](https://help.akeneo.com/en_US/discovering-px-insights/rating-reviews) (PX Insights (Rating & Reviews)): Explains the capabilities of PX Insights Ratings & Reviews, including sentiment analysis, feedback mapping, and displaying review signals in the Product Grid and Product Edit Form.

### `alloy_automation`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/alloy-integration-guide. Help centre: https://runalloy.com/ (sitemap); 0 articles read.

Functions:
- **Custom Workflows**: Merchants build automated sequences that connect triggers and actions to pass data between Yotpo and other apps
- **Prebuilt Recipes**: Merchants select ready-made workflow templates across marketing, customer service, and operations to automate tasks involving Yotpo
- **Workflow Triggers**: Starts an Alloy workflow when an event occurs in Yotpo Reviews or Yotpo Loyalty
- **Workflow Actions**: Executes tasks such as rewarding loyalty points or pushing data into Yotpo endpoints and downstream apps
- **App Authentication & Credentials**: Connects and authenticates Yotpo Reviews via OAuth and Yotpo Loyalty via API Key and GUID within Alloy

Accepted: none. the articles at https://runalloy.com/ show no text without a browser; a person picks the articles

### `ampifyme`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/ampifyme-integration-guide. Help centre: https://help.ampifyme.com/ (pages + sitemap); 18 articles read.

Functions:
- **AMP Product Details Page Reviews**: Displays Yotpo star ratings and customer reviews on mobile AMP product pages using the configured API key.
- **SERP Star Ratings Display**: Surfaces Yotpo customer ratings and review snippets on search engine result pages (SERPs) for instantly loading AMP pages.

Accepted:
- [How to add Product Reviews to AMP pages?](https://help.ampifyme.com/article/119-can-i-have-reviews-on-my-amp-pages) (AMP Product Details Page Reviews): Explains how to add and enable third-party review integrations on AMP product pages using the AMP Theme Editor.

### `antavo`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/antavo-integration-guide. Help centre: https://antavo.atlassian.net/ (—); 0 articles read.

Functions:
- **Gamified Reviews Module**: Connects to Yotpo using API credentials to automatically listen for customer reviews and award loyalty points.
- **Activity Point Scoring**: Defines rules and loyalty point amounts credited to customers when product reviews are submitted through Yotpo.
- **Rewards Management**: Allows customers to redeem loyalty points earned from Yotpo reviews for rewards like coupons, free samples, gift cards, and VIP events.

Accepted: none. the help centre at https://antavo.atlassian.net/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `attentive`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-reviews-with-attentive, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-attentive, Attentive help centre: Yotpo Reviews, Attentive help centre: Yotpo Review Request, Attentive help centre: Yotpo Loyalty & Referrals. Help centre: https://help.attentivemobile.com/hc/en-us (zendesk-search); 19 articles read.

Functions:
- **Journeys**: Triggers automated SMS and email communication flows from Yotpo review events (such as Review Completed or Review Request Eligible) and loyalty events (such as Points Earned or Tier Earned), using wait delays and branching logic.
- **Dynamic Segments**: Filters and groups subscribers using synced custom loyalty and review attributes such as point balances, VIP tier names, total review count, and star ratings.
- **Email Builder (Product Blocks)**: Displays live product star ratings and review counts inside email campaigns and journeys via Product Catalog, Product Recs, or Dynamic Products content blocks.
- **Sign-up Units**: Sends subscriber signup webhooks back to Yotpo when visitors subscribe via popups or landing pages, allowing Yotpo to award loyalty points or discounts based on earning rules.
- **Message Personalization & Dynamic Macros**: Inserts dynamic event data and profile properties into SMS and email templates, including unique review request links, product details, point balances, and VIP status.

Accepted:
- [Create a custom journey](https://help.attentive.com/hc/en-us/articles/360056870971-Create-a-custom-journey) (Journeys): Explains how to create a custom journey from scratch using triggers, steps, rules, and actions.
- [Create a dynamic segment](https://help.attentive.com/hc/en-us/articles/360051937411-Create-a-dynamic-segment) (Dynamic Segments): Explains the step-by-step process of creating dynamic subscriber segments using condition filters.
- [Add a product from your catalog to your email](https://help.attentive.com/hc/en-us/articles/8090356967188-Add-a-product-from-your-catalog-to-your-email) (Email Builder (Product Blocks)): Explains how to add and configure catalog product blocks, including layout and product details, within email campaigns and triggered journeys.
- [Get started with journeys](https://help.attentive.com/hc/en-us/articles/6425582978452-Get-started-with-journeys) (Journeys): Explains the core concepts, behavioral messaging capabilities, and trigger options for automated journeys.
- [Get started with sign-up units](https://help.attentive.com/hc/en-us/articles/6376556345876-Get-started-with-sign-up-units) (Sign-up Units): Explains how to use and configure sign-up units and landing pages to capture subscriber opt-ins.
- [Add dynamic product images to your triggered emails](https://help.attentive.com/hc/en-us/articles/6484695775380-Add-dynamic-product-images-to-your-triggered-emails) (Email Builder (Product Blocks)): Explains how to add dynamic product images and event data to triggered emails, including custom event data.
- [Manage sign-up units](https://help.attentive.com/hc/en-us/articles/54307937676052-Manage-sign-up-units) (Sign-up Units): Explains how to manage, edit, activate, duplicate, and schedule sign-up units.
- [Personalize Messages with Dynamic Content](https://help.attentive.com/hc/en-us/articles/4409633925780-Personalize-Messages-with-Dynamic-Content) (Message Personalization & Dynamic Macros): Explains how to insert dynamic personalization variables and macros into SMS and email message templates.
- [Create a segment from a custom attribute](https://help.attentive.com/hc/en-us/articles/6355344582804-Create-a-segment-from-a-custom-attribute) (Dynamic Segments): Explains how to create dynamic segments filtered by subscriber custom attributes.

### `bazaarvoice`

Read: Yotpo catalog card. Help centre: https://docs.bazaarvoice.com/home/en-us (pages); 14 articles read.

Functions:
- **Bazaarvoice Network Syndication**: Yotpo sends customer reviews and visual UGC to Bazaarvoice to be syndicated across retail channels.
- **Visual UGC Syndication**: Yotpo exports visual customer content to Bazaarvoice for display across third-party retailer product pages.
- **Product Review Syndication**: Yotpo provides ratings and review data to Bazaarvoice to deliver social proof to retail partner channels.

Accepted: none. the model accepted none of the 14 articles it read

### `bhn_rewards`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-rybbon, BHN Rewards (formerly Rybbon) page about Yotpo https://www.rybbon.net/yotpo-integration. Help centre: https://help.rybbon.net/hc/en-us (zendesk-search); 6 articles read.

Functions:
- **Campaign Webhook Setup**: Generates the webhook URL and webhook authentication key used to receive referral completion triggers and dispatch rewards.
- **Reward Approvals Queue**: Holds reward claims for manual merchant review and queues referrers when campaign reward inventory runs out.
- **Test Mode**: Allows merchants to simulate referral reward delivery with sample emails and dummy rewards before launching live.
- **Recipient Custom Fields**: Stores and displays additional recipient data passed from referral events in the campaign's Recipients and Reward Approval tabs.
- **Smart Global Rewards**: Curates reward catalogs and dynamically presents referrers with local digital gift cards and prepaid cards based on their country.
- **Email Branding and Sender Domain**: Customizes the reward email messaging and delivers referral rewards to recipients from an authorized brand domain.

Accepted: none. the model accepted none of the 6 articles it read

### `bigcommerce`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-bigcommerce, Yotpo guide https://support.yotpo.com/docs/bigcommerce-stencil-installing-yotpo-reviews-on-stencil. Help centre: https://support.bigcommerce.com/ (—); 0 articles read.

Functions:
- **Script Manager**: Used to inject the Yotpo JavaScript library into the storefront footer across all pages so widgets load properly.
- **Stencil Theme Files Editor**: Used to edit template components (such as product-view.html and card.html) to insert Yotpo Reviews and Star Rating widget code.
- **Built-in Product Reviews**: Must be disabled in Comments settings to avoid conflicting or duplicate review systems displaying alongside Yotpo.
- **Product Review Emails**: Must be disabled under Store Settings so BigCommerce does not send native review collection emails to customers.
- **Footer Scripts**: Used to paste the Yotpo Loyalty & Referrals loader script directly into the storefront footer.
- **Apps Marketplace**: Used to locate, install, and authorize Yotpo apps within the BigCommerce store admin.

Accepted: none. the help centre at https://support.bigcommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `blueconic`

Read: Yotpo catalog card, BlueConic page about Yotpo https://support-experiences.blueconic.com/en/articles/246955-yotpo-integration. Help centre: https://support-experiences.blueconic.com/en (pages); 20 articles read.

Functions:
- **Experiences**: Interactive experiences capture zero-party data and lead submissions that are passed to Yotpo to trigger loyalty point rewards and populate subscriber lists.
- **Custom Fields**: Used to configure custom action parameters (such as action_name) that pass to Yotpo to trigger specific custom earning rules.
- **Lead Opt-In and Privacy Filters**: Filters which collected customer leads are transmitted to Yotpo, restricting data to explicitly opted-in users or controlling the transfer of EU data.

Accepted:
- [Form screens (lead capture) overview](https://support-experiences.blueconic.com/en/articles/246905-form-screens-lead-capture-overview) (Experiences): This article explains how to add and configure form screens within an experience to capture first-party lead data and customer information.
- [Experience Creation Overview](https://support-experiences.blueconic.com/en/articles/246806-experience-creation-overview) (Experiences): This article explains the baseline steps required to create, name, and set up a new interactive experience in the builder.

### `bold_commerce`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/bold-commerce-integration-guide-for-reviews, Bold Commerce page about Yotpo https://blog.boldcommerce.com/yotpo-integration. Help centre: https://support.boldcommerce.com/en (pages); 15 articles read.

Functions:
- **Upsell and Cross-Sell Offers**: Displays Yotpo star ratings and reviews on Bold offer popups when customers add an item to the cart or upgrade a product.
- **Upsell Settings**: Enables the display of product star ratings on promotional offers inside the Bold Product Upsell app settings.

Accepted:
- [Create an Upsell Offer](https://support.boldcommerce.com/en/articles/15848518-create-an-upsell-offer) (Upsell and Cross-Sell Offers): Explains how to create and configure an upsell offer that displays an upgraded product pop-up when shoppers add or view trigger products.
- [Create a Cross-sell Offer](https://support.boldcommerce.com/en/articles/15848520-create-a-cross-sell-offer) (Upsell and Cross-Sell Offers): Explains how to configure cross-sell offers that recommend complementary products on product and cart pages.

### `boostcommerce`

Read: Yotpo catalog card, Boost Commerce page about Yotpo https://help.boostcommerce.net/article/392-yotpo, Boost Commerce help centre: Yotpo Integration Guide, Boost Commerce help centre: Yotpo 連携ガイド, Boost Commerce help centre: Yotpo integration guide. Help centre: https://support.boostcommerce.net/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Filter Trees (Review Ratings)**: Boost Commerce uses synchronized Yotpo rating data to enable a Review Ratings filter option, allowing shoppers to filter search and collection results by star rating.
- **Product Item (Product Rating Element)**: Boost Commerce displays Yotpo star ratings and review counts directly on product cards within search results and collection pages via visual design settings.
- **Sync Overview (Manual Sync)**: Merchants trigger a manual sync to pull the latest rating and review updates from Yotpo into Boost Commerce's search index.
- **Third-Party Product Review Settings**: Boost Commerce ingests Yotpo review and rating data after entering the Yotpo App Key and activating the provider under product review settings.
- **Product Item Liquid and JavaScript Templates (V2)**: Merchants modify Boost template files to change the display position of Yotpo review stars on product cards in V2 themes.

Accepted:
- [Filtering products by review rating](https://support.boostcommerce.net/en/articles/9355697-filtering-products-by-review-rating) (Filter Trees (Review Ratings)): This article explains how to create and configure a review rating filter option so shoppers can filter products by star ratings.
- [How to use the Sync features](https://support.boostcommerce.net/en/articles/9393595-how-to-use-the-sync-features) (Sync Overview (Manual Sync)): This article explains how to use the Sync Overview tab to manually trigger a sync of recent updates to immediately update product and app data.
- [How to customize the Product rating element](https://support.boostcommerce.net/en/articles/9393177-how-to-customize-the-product-rating-element) (Product Item (Product Rating Element)): This article explains how to add, position, and style the Product rating element within product items using the visual design settings.
- [For Dev - How to customize product item on collection/search page after filtering \(App Lib V2\)](https://support.boostcommerce.net/en/articles/9366214-for-dev-how-to-customize-product-item-on-collection-search-page-after-filtering-app-lib-v2) (Product Item Liquid and JavaScript Templates (V2)): This article explains how to customize product item rendering in App Lib V2 by editing template files like boost-pfs-filter-html.liquid and boost-pfs-filter.js.

### `braze`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/braze-integration-guide, Braze page about Yotpo https://www.braze.com/docs/partners/message_orchestration/channel_extensions/ecommerce/yotpo. Help centre: https://www.braze.com/docs (pages); 15 articles read.

Functions:
- **Connected Content**: Executes real-time API requests to Yotpo endpoints to dynamically pull star ratings, customer reviews, visual UGC, and loyalty balance into messages.
- **Liquid Personalization**: Evaluates conditional logic and renders the response data returned by Yotpo's API through Connected Content variables.
- **Email Campaigns**: Provides the campaign channel where marketers build messages and insert Yotpo Connected Content snippets into the email body.
- **Event Properties**: Passes dynamic event attributes such as product_id into Yotpo API URLs within Connected Content snippets.
- **Email Templates**: Stores pre-designed layouts where Yotpo Connected Content code snippets can be added and reused across email communications.

Accepted: none. the model accepted none of the 15 articles it read

### `brevo_pushowl`

Read: Yotpo catalog card, Brevo PushOwl page about Yotpo https://docs.pushowl.com/en/articles/14075206-yotpo-reviews-integration, Brevo PushOwl help centre: Yotpo Reviews Integration, Brevo PushOwl help centre: Yotpo Reviews Integration, Brevo PushOwl help centre: Yotpo reviews integration. Help centre: https://docs.pushowl.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Contact Attributes**: Receives and stores synced loyalty and referral metrics (such as points balance, VIP tier, referral link, and spend) on customer contact profiles via real-time and historical sync.
- **Automated Flows**: Triggers and powers automated email and SMS workflows when key loyalty and review events occur, such as reaching a new tier, earning points, or redeeming rewards.
- **Contact Segmentation**: Enables building targeted customer segments based on synced loyalty attributes such as total points balance, VIP tier name, total purchases, and completed referrals.
- **Template Personalization**: Dynamically inserts customer-level loyalty data (such as points balance, tier name, and referral links or codes) into email and SMS marketing templates.

Accepted:
- [Segmentation Builder Learn how to build an audience segment and the different conditions available to help you create highly specific segments.](http://docs.pushowl.com/en/articles/4113148-segmentation-builder) (Contact Segmentation): Explains how to use the Segmentation Builder to create targeted audience segments using conditions and AND/OR logic.
- [Customer Data Reference](http://docs.pushowl.com/en/articles/14642397-customer-data-reference) (Contact Attributes): Details the standard customer data properties and profile attributes synced and stored in Brevo PushOwl.
- [Attribute Mapping \(Custom Metafields\)](http://docs.pushowl.com/en/articles/14642962-attribute-mapping-custom-metafields) (Contact Attributes): Explains how to map custom data fields to Brevo PushOwl contact attributes to enable customer-level personalization and segmentation.
- [Adding Placeholders in Web Push Campaigns](http://docs.pushowl.com/en/articles/3211549-adding-placeholders-in-web-push-campaigns) (Template Personalization): Explains how to insert dynamic customer data placeholders and fallback text to personalize message templates.
- [Custom Events via Shopify Flow](http://docs.pushowl.com/en/articles/14645556-custom-events-via-shopify-flow) (Automated Flows): Explains how to track and pass custom event data into Brevo PushOwl to trigger automated marketing workflows.

### `builder_io`

Read: Yotpo catalog card, Builder.io page about Yotpo https://www.builder.io/c/docs/yotpo-app-template. Help centre: https://www.builder.io/ (pages + sitemap); 2 articles read.

Functions:
- **Visual Editor Drag-and-Drop**: Allows merchants to place and visually customize Yotpo product review widgets onto storefront pages without writing code.
- **Plugins Management**: Hosts the settings tile where merchants connect Yotpo to Builder.io using their Yotpo App Key.
- **Custom Component Inputs**: Supplies product context and custom inputs to Yotpo review blocks to display content for the correct product.
- **Targeting**: Uses plugin data and e-commerce context to display tailored page sections or review content to specific audience segments.
- **E-commerce Resource Previews**: Allows merchants to preview pages populated with specific product data and review widgets before publishing.

Accepted: none. the model accepted none of the 2 articles it read

### `cordial`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-cordial. Help centre: https://support.cordial.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Message Automations**: Receives triggers from Yotpo Loyalty events mapped via Cordial Message Keys to automatically send transactional loyalty and referral emails.
- **Custom Events and Event Data**: Receives real-time program events (such as points earned, tier changes, and referrals) and their associated properties to personalize email messages.
- **Contact Attributes**: Stores customer-specific loyalty and referral program attributes passed from Yotpo to enrich contact profiles for targeting.
- **API Keys and IP Allowlisting**: Authenticates and secures Yotpo's access to the Cordial account using generated API keys and allowed IP addresses.
- **Contact Subscription Status**: Governs the email opt-in state of users synced from Yotpo, defaulting new contacts to 'subscribed: none' while retaining existing 'subscribed' statuses.

Accepted:
- [Events](https://support.cordial.com/hc/en-us/articles/115005528508-Events) (Custom Events and Event Data): This article explains how Cordial stores and structures behavioral event data, including custom events and properties used to personalize messages and trigger automations.
- [Contact attributes](https://support.cordial.com/hc/en-us/articles/115005528368-Contact-attributes) (Contact Attributes): This article explains how contact attributes are stored in Cordial profiles across different data types to support audience segmentation, personalization, and automated messaging.
- [API keys](https://support.cordial.com/hc/en-us/articles/115005365087-API-keys) (API Keys and IP Allowlisting): This article explains how to create API keys in Cordial, configure their permissions, and allowlist IP addresses or CIDR ranges for secure API access.
- [Contact management](https://support.cordial.com/hc/en-us/articles/115005530808-Contact-management) (Contact Subscription Status): This article explains how Cordial manages contacts and channel subscription statuses, including how promotional and transactional messages are handled across different opt-in states.
- [Account contact attributes API](https://support.cordial.com/hc/en-us/articles/204570347-Account-contact-attributes-API) (Contact Attributes): This article explains the contact attributes schema in Cordial, detailing supported data types, indexing options, and rules for creating profile fields.
- [Automated messages](https://support.cordial.com/hc/en-us/articles/115005364287-Automated-messages) (Message Automations): This article explains how to create message automations in Cordial and configure key settings such as message keys, send triggers, and transactional classifications.

### `daasity`

Read: Yotpo catalog card, Daasity help centre: Yotpo, Daasity help centre: Integration Setup, Daasity help centre: Integration Specifications. Help centre: https://help.daasity.com/ (pages + llms.txt + sitemap); 19 articles read.

Functions:
- **Data Extractor**: Replicates reviews, customers, custom fields, and products data from Yotpo endpoints into Daasity database tables via UPSERT.
- **Historical Data Loading**: Backfills historical review, customer, and product records from Yotpo into the data warehouse during initial setup.
- **Transformation Configuration**: Transforms and models raw extracted Yotpo review and loyalty statistics into analytics-ready schemas.
- **Workflow Configuration**: Manages automated execution schedules for extracting and processing incoming Yotpo data.
- **Data Warehouse Tables and ERD**: Houses normalized tables for Yotpo reviews, custom fields, and customer loyalty statistics, maintaining relationship keys across tables.
- **Customer Segmentation and Analytics**: Uses Yotpo review scores, sentiment, and loyalty point metrics alongside order data to segment customers and evaluate sales performance.

Accepted:
- [Workflows & Scheduling](https://help.daasity.com/technical-docs/workflows-and-scheduling) (Workflow Configuration): Explains how Daasity workflows operate as automated pipelines that schedule and chain data extraction and transformation jobs.
- [Transform Code](https://help.daasity.com/technical-docs/transform-code) (Transformation Configuration): Explains how SQL files and YAML script manifests are organized in a code repository and run via workflows to transform raw data into analytical models.
- [Getting Started with Workflows](https://help.daasity.com/technical-docs/workflows-and-scheduling/getting-started-with-workflows) (Workflow Configuration): Explains the purpose of workflows in orchestrating extractions and SQL transformations, including the automatic configuration of the daily incremental workflow.

### `daitafix`

Read: Yotpo catalog card, DaitaFix page about Yotpo https://daitafix.com/yotpo/setup. Help centre: https://daitafix.com/ (—); 0 articles read.

Functions:
- **Centralized AI Engine**: Ingests synced customer reviews and sentiment data from Yotpo to build brand context and improve AI readability across large language models.
- **GEO Score Dashboard**: Layers analytics over Yotpo social proof and review sentiment to monitor AI visibility and identify revenue-impacting gap priorities.
- **Structured Data Generation**: Uses review data and brand context to generate schema.org markup and llms.txt files so AI search platforms can interpret review proof.
- **Content Theatre**: Applies insights from review sentiment gaps to generate automated content fixes for product pages, FAQs, and store schema.

Accepted: none. the help centre at https://daitafix.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `datagrail`

Read: Yotpo catalog card, DataGrail help centre: Yotpo. Help centre: https://docs.datagrail.io/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Request Manager**: Processes automated data subject requests (DSRs/DSARs) by querying Yotpo via API to locate and retrieve data associated with consumer email identifiers.
- **Access Request Lifecycle**: Executes synchronous access requests against Yotpo to compile the consumer's personal data into fulfillment reports.
- **Intake Forms**: Collects consumer identity details (such as email addresses) and privacy requests that trigger automated lookups in Yotpo.
- **System Detection and Data Discovery**: Discovers and maps customer personal data stored within Yotpo to maintain real-time visibility into privacy data footprint.
- **Consent and Preference Management**: Tracks and manages consumer privacy choices and consent policies related to data processed across connected platforms.

Accepted:
- [Request Manager](https://docs.datagrail.io/docs/request-manager/getting-started) (Request Manager): Explains the foundational connections and integration configuration required to process data privacy requests in Request Manager.
- [Privacy Request Center](https://docs.datagrail.io/docs/request-manager/request-intake/privacy-request-center) (Intake Forms): Explains how the Privacy Request Center serves as a customizable, hosted intake form that adapts to consumer geolocation to collect privacy requests.
- [System Detection](https://docs.datagrail.io/docs/ldm/system-detection) (System Detection and Data Discovery): Explains how System Detection scans systems of record and connected software to automate data mapping and identify third-party services.
- [Access Request Lifecycle](https://docs.datagrail.io/docs/request-manager/request-processing/privacy-right/access) (Access Request Lifecycle): Explains the full submission workflow and initialization lifecycle for consumer access (right to know) requests.
- [Consent](https://docs.datagrail.io/docs/consent/overview) (Consent and Preference Management): Provides an overview of the Consent Management Platform, detailing user roles and automated banner configurations for script and cookie compliance.
- [Responsible Data Discovery & Classification](https://docs.datagrail.io/docs/ldm/rdd/overview) (System Detection and Data Discovery): Explains how Responsible Data Discovery detects, categorizes, and maps personal data across structured data sources and third-party applications.
- [Consent Policies](https://docs.datagrail.io/docs/consent/settings/consent-policies) (Consent and Preference Management): Explains how policy configurations govern online tracking behavior and offline privacy choices based on consumer geolocation.
- [Processing Overview](https://docs.datagrail.io/docs/request-manager/request-processing/overview) (Request Manager): Explains how privacy managers search, review, and handle requests across their processing states within the Request Manager portal.

### `dialogue`

Read: Yotpo catalog card, Dialogue page about Yotpo https://help.nowdialogue.com/en/articles/9929014-yotpo-reviews-dialogue-integration, Dialogue page about Yotpo https://help.nowdialogue.com/en/articles/9569370-yotpo-loyalty-dialogue-integration, Dialogue page about Yotpo https://help.nowdialogue.com/en/articles/9929012-yotpo-visual-ugc-dialogue-integration. Help centre: https://help.nowdialogue.com/en (—); 0 articles read.

Functions:
- **Product Recommendations**: Displays Yotpo product reviews, UGC, and rating data directly within personalized product recommendation carousels and widgets.
- **On-Site Personalized Experiences**: Utilizes Yotpo loyalty and UGC data to personalize dynamic on-site banners, widgets, and tailored customer engagement touchpoints.
- **A/B Testing**: Tests and optimizes different variations of on-site personalized experiences and product recommendations powered by Yotpo data to improve conversion rates.

Accepted: none. the help centre at https://help.nowdialogue.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `digioh`

Read: Yotpo catalog card, Digioh page about Yotpo https://get.digioh.com/yotpo, Digioh page about Yotpo https://help.digioh.com/knowledgebase/digioh-yotpo-integration. Help centre: https://help.digioh.com/knowledgebase (—); 0 articles read.

Functions:
- **Digioh Quizzes**: Provides hosted quizzes that customers complete to trigger and earn Yotpo Loyalty points.
- **Rating Stars Element**: Displays Yotpo-generated review star ratings alongside recommended products inside Digioh quiz results.
- **Campaign Integrations**: Attaches an external webhook or pipeline to a Digioh campaign to pass quiz completion events to Yotpo Loyalty.
- **Custom Product Feed**: Populates dynamic product recommendations in quiz outcomes where Yotpo ratings are displayed.
- **Button Actions**: Executes form submission and completion events on quiz end screens that trigger Yotpo points rewards.

Accepted: none. the help centre at https://help.digioh.com/knowledgebase could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `dixa`

Read: Yotpo catalog card, Dixa page about Yotpo https://support.dixa.help/en/articles/1879-yotpo-integration, Dixa help centre: Yotpo reviews, Dixa help centre: Yotpo in automations, Dixa help centre: Yotpo in mim. Help centre: https://support.dixa.help/en (sitemap); 20 articles read.

Functions:
- **Conversation Cards**: Displays customer profile details, user-generated content and product reviews, and loyalty points, tiers, and referral data directly in the agent conversation view.
- **Reviews Channel**: Ingests reviews matching a star rating threshold as chat conversations and syncs public agent replies and edited responses back to the Yotpo review widget.
- **Automations Platform Actions**: Retrieves customer profiles, loyalty status, or review summaries in automated flows using email or phone number to set flow variables, evaluate conditions, or update attributes.
- **Mim AI Agent Tools**: Empowers AI agents to query loyalty balances, VIP tiers, or review history as automated tools during conversations based on custom instructions and procedures.
- **Queues**: Routes incoming review conversations to designated agent queues based on review channel configuration.

Accepted:
- [Mim tool platform actions](https://support.dixa.help/en/articles/2118-mim-tool-platform-actions) (Mim AI Agent Tools): Explains how to configure platform actions as tools for Mim AI agents, including setting tool parameters, values, and instructions.
- [Getting started with automations](https://support.dixa.help/en/articles/257-getting-started-with-automations) (Automations Platform Actions): Explains how Dixa automations work, including configuring automation flows with triggers, conditions, and actions.
- [Configurable conversation sidebar](https://support.dixa.help/en/articles/2148-configurable-conversation-sidebar) (Conversation Cards): Explains how to organize and configure cards in the right-side conversation sidebar, including conditional card visibility.
- [Mim actions](https://support.dixa.help/en/articles/1915-mim-actions) (Mim AI Agent Tools): Explains how to create and configure Mim actions to allow the AI agent to query internal systems and take action based on descriptions and instructions.

### `dondy`

Read: Yotpo catalog card, Dondy page about Yotpo https://www.dondy.net/post/how-to-send-whatsapp-review-requests-using-yotpo-with-dondy, Dondy page about Yotpo https://www.dondy.net/post/how-to-send-whatsapp-thank-you-messages-after-yotpo-reviews-using-dondy-shopify-flow. Help centre: https://help.dondy.net/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **WhatsApp Review Request Flows**: Triggers automated WhatsApp messages after order fulfillment containing a button that directs customers to leave a Yotpo review.
- **Shopify Flow Operational Automation Templates**: Creates customizable WhatsApp message templates with dynamic shortcodes that generate a Template ID used for post-review follow-ups.
- **Send a WhatsApp Message via Dondy (Shopify Flow Action)**: Executes WhatsApp sends using mapped Yotpo review data, including reviewer name, reviewer email, and review rating.
- **WhatsApp Message Template Approval**: Submits and verifies review request and post-review thank-you message templates for WhatsApp approval before flows can send.

Accepted:
- [What automations can you build with Dondy?](https://help.dondy.net/message-customers/8tTwAB5stPocKLWpoeG7Uj/what-automations-can-you-build-with-dondy/8rDHseRyg1Pidpt8gA3kDo) (Shopify Flow Operational Automation Templates): Explains how to configure operational automation templates in Dondy using dynamic Shopify Flow variables and obtain the unique Template ID required for Shopify Flow actions.
- [Start a conversation with a Message Template](https://help.dondy.net/inbox--ai-agent/8tTwAB5stQukdVaYjH3VjZ/start-a-conversation-with-a-message-template/8rDHseRyg1XfQ139N26S2M) (WhatsApp Message Template Approval): Explains how WhatsApp message templates are created in Dondy, automatically submitted to Meta for review, and verified before they can be used to send messages.

### `dotdigital`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/dotdigital-integration-guide-for-yotpo-reviews, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital, Dotdigital page about Yotpo https://support.dotdigital.com/en/articles/8199787-integrate-yotpo-reviews-with-dotdigital, Dotdigital page about Yotpo https://support.dotdigital.com/en/articles/8199790-use-yotpo-review-data-in-dotdigital, Dotdigital page about Yotpo https://support.dotdigital.com/en/articles/8199358-add-yotpo-reviews-to-campaigns-pages-and-forms, Dotdigital page about Yotpo https://support.dotdigital.com/en/articles/12674501-integrate-yotpo-loyalty-with-dotdigital, Dotdigital help centre: Add Yotpo reviews to campaigns, pages, and forms, Dotdigital help centre: Integrate Yotpo Reviews with Marketing, Dotdigital help centre: Use Yotpo App blocks in EasyEditor. Help centre: https://marketing.help.dotdigital.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Programs**: Enrolls contacts into automated customer journeys upon submitting a product review or when triggered by Yotpo Loyalty events, and routes contacts using decision nodes based on review feedback.
- **Insight data**: Stores synced product review details (such as ratingscore, ratingcontent, productid, and brand) against contact records in a dedicated Reviews collection.
- **Segments**: Allows merchants to filter contacts using Yotpo review insight data (e.g., rating score thresholds) and loyalty attributes to target email and SMS campaigns.
- **Contact data fields**: Receives synced customer loyalty and referral attributes from Yotpo (such as points_balance, current_tier, referral_code, and points_expire_at) to enrich contact profiles.
- **EasyEditor App blocks**: Provides drag-and-drop review blocks in EasyEditor to pull and display 5-star product reviews directly in email campaigns, pages, and forms.

Accepted:
- [EasyEditor extensions: App blocks overview](https://marketing.help.dotdigital.com/en/articles/8199355-easyeditor-extensions-app-blocks-overview) (EasyEditor App blocks): Explains how App blocks from partner integrations are added to an account and converted into drag-and-drop blocks within EasyEditor.
- [View a contact's Insight data](https://marketing.help.dotdigital.com/en/articles/8198762-view-a-contact-s-insight-data) (Insight data): Explains how to view contact-scoped Insight data collections and individual records on a contact's profile in the Single customer view.
- [The non-developers' guide to Insight data](https://marketing.help.dotdigital.com/en/articles/8199279-the-non-developers-guide-to-insight-data) (Insight data): Explains what Insight data is, how contact-scoped collections and records are structured, and how they enrich customer profiles for marketing.
- [Edit a contact's data fields](https://marketing.help.dotdigital.com/en/articles/8198834-edit-a-contact-s-data-fields) (Contact data fields): Explains how to locate, view, and edit standard and custom contact data fields within the Single customer view.
- [Use Insight data for segmentation](https://marketing.help.dotdigital.com/en/articles/8199282-use-insight-data-for-segmentation) (Segments): Explains how to use contact Insight data collections and objects to create targeted segment rules.
- [Create, delete, and edit custom data fields](https://marketing.help.dotdigital.com/en/articles/8198833-create-delete-and-edit-custom-data-fields) (Contact data fields): Explains how custom data fields work in Dotdigital, including field types, limits, and how they store contact-level attributes.
- [Create a segment](https://marketing.help.dotdigital.com/en/articles/8198789-create-a-segment) (Segments): Explains how to build a new segment using criteria rules and logic blocks in the Dotdigital segment builder.

### `dotdigital_personalization`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/fresh-relevance-integration-guide-for-reviews, Dotdigital page about Yotpo https://personalization.help.dotdigital.com/en/articles/8523333-import-review-data. Help centre: https://personalization.help.dotdigital.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Recommendation SmartBlocks**: Displays imported star ratings and review counts alongside AI-powered product recommendations across emails and web pages.
- **Rating and Review Provider Channel Settings**: Configures review data ingestion, defines review key matching (SKU, prid, rid), and toggles detailed versus aggregated reviews.
- **Social Proof Module**: Serves as the required platform module to enable review imports and combine review scores with social proof messaging.
- **Product Catalog and Identifier Mapping**: Stores product identifiers (such as prid, SKU, or rid) that match incoming review data to specific catalog products.
- **Site and Service Reviews**: Ingests store-level and service-level ratings and reviews to display overall brand trust across channels.

Accepted:
- [Import review data](https://personalization.help.dotdigital.com/en/articles/8523333-import-review-data) (Rating and Review Provider Channel Settings): Explains how to set up an external rating and review provider channel, map review keys, and select whether to import product or site reviews.
- [Recommendation SmartBlocks](https://personalization.help.dotdigital.com/en/articles/8523414-recommendation-smartblocks) (Recommendation SmartBlocks): Explains how Recommendation SmartBlocks work, their placement options across email and web, and use cases for displaying personalized recommendations.
- [Social proof messaging](https://personalization.help.dotdigital.com/en/articles/8523439-social-proof-messaging) (Social Proof Module): Explains how to configure social proof messaging within recommendations based on thresholds of real-time browsing, carting, and purchasing activity.
- [Reviews SmartBlocks](https://personalization.help.dotdigital.com/en/articles/8523449-reviews-smartblocks) (Site and Service Reviews): Explains how to create and configure Reviews SmartBlocks to display product, site, or service reviews across marketing channels.
- [Import product data](https://personalization.help.dotdigital.com/en/articles/8523325-import-product-data) (Product Catalog and Identifier Mapping): Explains how to format and import product catalog data, including product identifiers, into Dotdigital Personalization.
- [Product variants \(SKUs\)](https://personalization.help.dotdigital.com/en/articles/8523669-product-variants-skus) (Product Catalog and Identifier Mapping): Explains how Dotdigital structures and identifies catalog items using base Product IDs and variant SKUs.

### `ecocart`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/ecocart-integration-guide-for-loyalty-referrals-and-smsbump. Help centre: https://support.ecocart.io/knowledge (—); 0 articles read.

Functions:
- **Carbon Neutral Order Product**: EcoCart generates a dedicated Carbon Neutral Order product in the store's ecommerce catalog, whose product ID is targeted by Yotpo Loyalty to award points or offer free offset redemptions.
- **Cart Carbon Offset Application**: EcoCart applies carbon offset line items to the cart, which triggers Yotpo purchase-based loyalty points or receives offset items redeemed through Yotpo loyalty rewards.

Accepted: none. the help centre at https://support.ecocart.io/knowledge could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `ecomposer`

Read: Yotpo catalog card, EComposer page about Yotpo https://help.ecomposer.io/docs/extensions-integrations/third-party-extensions/yotpo-reviews. Help centre: https://help.ecomposer.io/docs (pages); 17 articles read.

Functions:
- **Extensions Manager**: Allows merchants to search for, install, and manage the Yotpo Widget and Rating extensions inside the EComposer editor.
- **Reviews Widget Extension**: Renders customer reviews and the interactive review submission form directly within product templates or review tabs.
- **Star Ratings Extension**: Displays average product star ratings and review counts calculated from review data, typically placed near the product price.
- **Product Grid and Related Products Sections**: Displays third-party star ratings across catalog items and recommendations by enabling the third-party review app setting.

Accepted:
- [Extension Overview](https://help.ecomposer.io/docs/extensions-integrations/extension-overview) (Extensions Manager): It explains how to access the CRO Extensions dashboard to browse, search, filter, install, and manage third-party app extensions within the EComposer editor.

### `emarsys`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-emarsys. Help centre: https://help.emarsys.com/hc/en-us (zendesk-search); 0 articles read.

Functions:
- **Automation Center**: Merchants create event-based automated programs using the External Event entry point to trigger customer journeys based on Yotpo loyalty and referral actions.
- **External Events**: Yotpo sends loyalty and referral milestones (such as points earned, tier updates, or referral completions) as external events to Emarsys.
- **Contact Data and Custom Fields**: Yotpo creates and updates customer profiles with loyalty attributes and program data across contact fields via API.
- **API Users and Security Settings**: Merchants configure an API user with WSSE authentication and grant specific endpoint permissions (field, event, contact, customer) to connect Yotpo.

Accepted: none. the help centre at https://help.emarsys.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `fast_simon`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/fast-simon-integration-guide. Help centre: https://www.fastsimon.com/ (—); 0 articles read.

Functions:
- **Instant Search and Search Results**: Displays Yotpo star ratings and product reviews directly on product cards in instant search and search results pages.
- **Product Filters**: Allows shoppers to refine search results and navigation listings by Yotpo review ratings.
- **Sorting Options**: Enables shoppers to sort search and navigation product listings by Yotpo review score.
- **Smart Navigation**: Embeds Yotpo ratings, reviews, sorting, and filtering into category and collection navigation pages.
- **Merchandising**: Incorporates Yotpo review ratings to power automated or rule-based product merchandising and ranking.

Accepted: none. the help centre at https://www.fastsimon.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `findify`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/findify-integration-guide, Findify page about Yotpo https://developers.findify.io/docs/third-party-yotpo. Help centre: https://developers.findify.io/docs (—); 0 articles read.

Functions:
- **Search Results and Live Search**: Displays Yotpo star ratings and review counts directly in the live search dropdown and search result product listings.
- **Smart Category Filtering**: Enables shoppers to filter search results and collection pages based on synced Yotpo star ratings.
- **Product Recommendations**: Shows Yotpo star ratings alongside recommended products to provide social proof.
- **Compatible Apps Settings**: Merchant dashboard section where the review app connection is toggled on to sync rating data.

Accepted: none. the help centre at https://developers.findify.io/docs could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `fomo`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/fomo-integration-guide. Help centre: https://fomo.family/ (—); 0 articles read.

Functions:
- **Notification Message Customization**: Formats imported Yotpo product review data into customized social proof notification text displayed on the storefront.
- **Minimum Star Rating Filter**: Filters incoming Yotpo reviews so only reviews that meet or exceed the selected star threshold are displayed.
- **Notification Design and Branding**: Controls the visual appearance, styling, and branding of the social proof notifications showcasing Yotpo reviews.
- **Review Event Import**: Polls and ingests new product reviews every 30 minutes via API keys to generate notification events.

Accepted: none. the help centre at https://fomo.family/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `gempages`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/gempages-integration-guide, GemPages page about Yotpo https://help.gempages.net/articles/add-yotpo-product-reviews, GemPages help centre: How to add yotpo loyalty rewards form to instant landing page, GemPages help centre: Add yotpo product reviews custom pages, GemPages help centre: Yotpo product reviews ugc. Help centre: https://help.gempages.net/ (pages + sitemap); 20 articles read.

Functions:
- **Library (Third-Party Elements)**: Allows merchants to search for, configure, and add the Yotpo Product & Collection or Custom Pages elements into their active GemPages element toolbar.
- **Drag-and-Drop Page Editor**: Provides the visual workspace where merchants position and structure Yotpo widget elements across product, collection, and custom pages.
- **Element Settings Panel**: Provides the 'Choose Widget' dropdown and configuration controls to select and customize which Yotpo widget displays (Star Rating, Separated Q&A, Reviews Highlight, or Reviews Carousel).
- **Page Publishing and Preview**: Saves, previews, and publishes page designs to the live Shopify store, embedding the Yotpo scripts and rendering review data.
- **Instant Landing Pages**: Enables standalone or headless landing pages where merchants can embed Yotpo Loyalty & Rewards forms and custom review widgets.

Accepted:
- [V7 integrate third party app](https://help.gempages.net/articles/v7-integrate-third-party-app) (Library (Third-Party Elements)): Explains how to search for, activate, and integrate third-party application elements into the GemPages editor.
- [Page actions save preview publish](https://help.gempages.net/articles/page-actions-save-preview-publish) (Page Publishing and Preview): Explains how to save page drafts, preview designs, and publish updates live to your store in GemPages.
- [Introduction to library](https://help.gempages.net/articles/introduction-to-library) (Library (Third-Party Elements)): Explains how to navigate the GemPages Library to find and add elements to the editor toolbar.

### `gladly`

Read: Yotpo catalog card, Gladly page about Yotpo https://help.gladly.com/docs/yotpo-on-app-platform, Gladly help centre: Yotpo on App Platform Overview, Gladly help centre: Yotpo on App Platform Installation. Help centre: https://help.gladly.com/docs (pages + llms.txt); 16 articles read.

Functions:
- **Customer Profile Cards**: Displays Yotpo Loyalty & Referrals data and customer reviews directly alongside the customer conversation.
- **Agent Actions**: Enables agents to submit actions back to Yotpo—adjusting points, crediting loyalty campaigns, and replying to reviews—from the conversation compose menu.
- **Rules and Routing**: Uses Yotpo customer attributes such as VIP tier, points balance, and review ratings to automatically prioritize and route conversations.
- **Gladly AI and Guides**: Utilizes Yotpo loyalty, review, and referral context to provide personalized automated responses and execute loyalty actions in workflows.
- **App Developer Tools (App Platform)**: Connects external apps and manages app-level configurations, such as review fetch limits and loyalty point adjustment boundaries.

Accepted:
- [Custom Attributes for Routing and People Match](https://help.gladly.com/docs/custom-attributes-for-routing-and-people-match) (Rules and Routing): This article explains how custom attributes from external systems can be used within Gladly rule conditions and People Match to route and prioritize conversations.
- [Organize the Customer Profile](https://help.gladly.com/docs/organize-the-customer-profile) (Customer Profile Cards): This article explains how to add, remove, and organize custom attribute and App Platform cards on the Customer Profile.
- [Set up Agent Actions](https://help.gladly.com/docs/add-agent-actions) (Agent Actions): This article explains how to configure and expose App Platform actions in the conversation Plus menu so agents can execute external tasks directly from a customer profile.
- [Manage Custom and External Apps](https://help.gladly.com/docs/gladly-apps) (App Developer Tools (App Platform)): This article explains how administrators can manage, install, and configure external and custom applications within the App Platform settings.
- [Add an Action to Guide Sections](https://help.gladly.com/docs/author-actions) (Gladly AI and Guides): This article explains how to attach App Platform actions to Guide sections so AI workflows can retrieve or update external data during customer interactions.

### `glew`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/glew-integration-guide, Glew page about Yotpo https://www.glew.io/articles/4-ecommerce-apps-you-need, Glew page about Yotpo https://www.glew.io/integrations/yotpo. Help centre: https://www.glew.io/ (pages + sitemap); 20 articles read.

Functions:
- **Customer Segmentation**: Receives review activity, ratings, and loyalty campaign data to filter and build customer segments
- **Custom Dashboards**: Visualizes imported Yotpo review and loyalty metrics alongside multichannel KPIs
- **Automated and Custom Reports**: Combines Yotpo reviews, ratings, and loyalty activity with sales metrics to track impact on CLTV, AOV, and ROI
- **Segment Push to ESP**: Pushes segments created with Yotpo review and loyalty data directly to connected email service providers
- **Store Settings**: Accepts Yotpo API credentials and GUID to authenticate and import reviews and loyalty data

Accepted: none. the model accepted none of the 20 articles it read

### `gogenerosity`

Read: Yotpo catalog card, GoGenerosity page about Yotpo https://help.gogenerosity.com/how-to-donate-yotpo-loyalty-points, GoGenerosity help centre: How to donate yotpo loyalty points. Help centre: https://help.gogenerosity.com/ (pages + sitemap); 20 articles read.

Functions:
- **Loyalty donation product generation**: GoGenerosity creates a dedicated donation product in Shopify tagged with 'loyalty' and 'donation' that Yotpo attaches to a Free Product reward.
- **Donation tracking and reporting**: GoGenerosity tracks redemptions and reports on point donations using the automated 'loyalty' and 'donation' vendor tags applied to the redeemed product.
- **Multiple charity partner allocation**: GoGenerosity handles the backend charity setup and evenly splits point donation proceeds when customers redeem points across multiple charity products.

Accepted:
- [Smile.io help article](https://help.gogenerosity.com/smile.io-help-article) (Loyalty donation product generation): Explains how to generate and customize the dedicated GoGenerosity loyalty donation product in Shopify with its automated vendor tags.

### `gorgias`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/gorgias-integration-guide-for-reviews-and-loyalty-referrals, Gorgias page about Yotpo https://www.gorgias.com/blog/yotpo-integration, Gorgias help centre: Yotpo, Gorgias help centre: Yotpo customer data 380029. Help centre: https://docs.gorgias.com/en-US (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Customer Sidebar Widgets**: Displays Yotpo customer insights next to tickets, including VIP tier, loyalty point balances, redemptions, referral stats, review history, average ratings, and AI sentiment.
- **Tickets**: Automatically creates new helpdesk tickets when a customer submits a product review or when reviews/Q&A are escalated, containing score, product, and review details.
- **Ticket Replies (Public and Private)**: Enables agents to send a public comment or private response to a Yotpo review directly from the ticket editor without opening Yotpo.
- **Macros**: Provides pre-written responses and automated actions that agents apply based on customer review sentiment, star ratings, or loyalty status (e.g., sending discount codes to dissatisfied shoppers).
- **Email Channel and Forwarding**: Receives escalated reviews and customer questions forwarded to the Gorgias support email address, routing replies back to the reviewer's unique Yotpo reply-to address.
- **Internal Notes**: Allows agents to collaborate internally on a ticket, serving as a message activity event that triggers a sync of updated Yotpo loyalty data.

Accepted:
- [Email: Connect your email and set up automatic forwarding](https://docs.gorgias.com/en-US/send-and-receive-email-from-gorgias-using-automatic-forwarding-1656317) (Email Channel and Forwarding): Explains how to connect an external support email address to Gorgias using automatic forwarding so incoming customer messages centralize as tickets and outbound replies route properly.
- [Add internal notes to tickets](https://docs.gorgias.com/en-US/internal-notes-81888) (Internal Notes): Explains how agents can leave internal notes within ticket threads visible only to the team and how to switch to the internal note channel composer.
- [Connect external apps to Gorgias and create sidebar widgets](https://docs.gorgias.com/en-US/connect-external-apps-to-gorgias-and-create-sidebar-widgets-81822) (Customer Sidebar Widgets): Explains how to connect external applications and APIs to Gorgias to bring third-party data directly into the customer sidebar widgets alongside tickets.
- [Macros: Create and manage macros](https://docs.gorgias.com/en-US/macros-101-81846) (Macros): Explains how to create, configure, and manage macros to automate replies and trigger ticket actions.
- [Create a ticket](https://docs.gorgias.com/en-US/create-a-ticket-81831) (Tickets): Explains what a ticket is in Gorgias and provides steps for creating and sending tickets from scratch across support channels.
- [Use variables in macros](https://docs.gorgias.com/en-US/macro-variables-101-81845) (Macros): Explains how to insert dynamic variables into macros to auto-populate customer, ticket, and integration data into responses.

### `heartland_retail_by_hyperspace`

Read: Yotpo catalog card, Heartland Retail by Hyperspace help centre: Omnichannel Loyalty Integration with Heartland Retail. Help centre: https://hyperspace.zendesk.com/hc/en-us (zendesk-search); 12 articles read.

Functions:
- **Hyperspace Order Exclusion Settings**: Configures rules in Hyperspace to exclude synced online sales orders from earning loyalty points a second time in the POS.
- **POS Points Redemption**: Allows retail cashiers in Heartland Retail POS to look up customer loyalty accounts and apply point-based discounts or rewards to in-store purchases.
- **Sales Order Source Tracking**: Assigns order source values to Heartland Retail sales orders so the system can distinguish between online and in-store transactions when awarding points.

Accepted:
- [Omnichannel Loyalty Integration with Heartland Retail](https://support.hyperspacehq.com/hc/en-us/articles/35972452016667-Omnichannel-Loyalty-Integration-with-Heartland-Retail) (Hyperspace Order Exclusion Settings): This article explains how Hyperspace settings prevent duplicate loyalty rewards by excluding online-originated orders from earning points again when synced into the Heartland Retail POS.

### `hubspot`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-hubspot, Yotpo guide https://support.yotpo.com/docs/hubspot-integration-guide-for-reviews. Help centre: https://knowledge.hubspot.com/ (pages + sitemap); 20 articles read.

Functions:
- **Workflows**: Enrolls contacts to trigger automated loyalty emails via workflow IDs and sends automated site review request emails.
- **Contact Properties**: Stores synced loyalty data under Swell Information and review metrics under the Yotpo property group on contact records.
- **Marketing Emails**: Builds and sends marketing campaigns populated with loyalty personalization data or generated from review request templates.
- **Design Manager**: Hosts and publishes synced coded template files such as the site review request HTML file.
- **Lists**: Segments audiences based on synced customer review ratings, review activity, and loyalty program status.
- **Contact Records**: Stores individual shopper profiles, creates new records for referral share events, and requires existing records to sync other event data.

Accepted:
- [HubSpot's default contact properties](https://knowledge.hubspot.com/properties/hubspots-default-contact-properties) (Contact Properties): Explains how contact properties work to store information on contact records in HubSpot and how to locate and view them.

### `insider`

Read: Yotpo catalog card, Insider page about Yotpo https://academy.useinsider.com/docs/external-platform-integrations-yotpo, Insider page about Yotpo https://academy.useinsider.com/docs/sending-yotpo-data-to-insider, Insider help centre: Yotpo, Insider help centre: Send Yotpo Data to Insider One. Help centre: https://academy.insiderone.com/docs (pages + llms.txt); 20 articles read.

Functions:
- **Dynamic Segments**: Merchants filter and segment audiences in InOne using synced Yotpo customer attributes and events, such as point balances, redemptions, review sentiment, and VIP tiers.
- **Journeys**: Merchants build automated cross-channel customer journeys triggered or guided by Yotpo loyalty milestones and review events, such as gaining or losing VIP status.
- **External Platform Integrations**: The administrative interface within InOne where authorized users (Admin or Editor with PII access) connect the external platform and manage the historical and ongoing data sync.
- **Multi-Channel Messaging Suite**: Merchants craft and send personalized communications across Email, SMS, WhatsApp, Web Push, and App Push using Yotpo loyalty and sentiment data.
- **User Attributes and Profiles**: InOne ingests and stores Yotpo user properties and historical data—including points earned, balance, redemptions, and average review sentiment—on customer profiles.

Accepted:
- [External Platform Integration Guide](https://academy.insiderone.com/docs/external-platform-integration-guide-1) (External Platform Integrations): Explains how to use the Insider Integration Hub to set up, download user data lists for, and manage external third-party platform integrations.
- [Dynamic Segments](https://academy.insiderone.com/docs/dynamic-segments) (Dynamic Segments): Explains how dynamic segments function as real-time, auto-updating audience lists based on event and attribute rules.
- [Unified Customer Database](https://academy.insiderone.com/docs/unified-customer-database-ucd) (User Attributes and Profiles): Explains how the Unified Customer Database collects, unifies, and stores customer attributes and behavioral events from external sources on individual profiles.
- [Anatomy of an Email Campaign](https://academy.insiderone.com/docs/anatomy-of-an-email-campaign) (Multi-Channel Messaging Suite): Explains the structure of an email campaign, including how to configure recipient lists, apply segments, and target audiences.
- [Architect](https://academy.insiderone.com/v1/docs/introduction-to-architect) (Journeys): Explains how Architect works as Insider's customer journey builder to automate and orchestrate omnichannel marketing flows using unified customer data.
- [Elements of a User Profile](https://academy.insiderone.com/docs/elements-of-a-user-profile) (User Attributes and Profiles): Explains the structure of user profiles, detailing how real-time events and attributes from the Unified Customer Database are displayed across profile sections.

### `judge_me`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-loyalty-referrals-and-judgeme, Judge.me page about Yotpo https://support.judge.me/support/home. Help centre: https://judge.me/help/en (pages); 15 articles read.

Functions:
- **Judge.me Reward Conditions**: Filters which submitted reviews (by reviewer verification status and review content such as text or photos) qualify to trigger Yotpo's judgeme_review loyalty action.
- **Judge.me Rewards App Integration Settings**: Enables coupon rewards and stores Yotpo Loyalty credentials (Merchant ID and API Key) to route completed review events to Yotpo.
- **Judge.me Review Widget**: Captures customer review submissions, ratings, and media on the storefront that serve as the qualifying actions for earning Yotpo loyalty points.

Accepted:
- [Connect Judge.me with third-party apps using integrations](https://judge.me/help/en/articles/8363837-connect-judge-me-with-third-party-apps-using-integrations) (Judge.me Rewards App Integration Settings): This article explains how to navigate to the integrations settings in Judge.me to locate and connect third-party loyalty and rewards applications.
- [Adding the Review Widget on your product page](https://judge.me/help/en/articles/11424925-adding-the-review-widget-on-your-product-page) (Judge.me Review Widget): This article explains how to add and configure the Judge.me Review Widget on product pages using Shopify app embeds and theme blocks.
- [Offering Judge.me-generated coupon codes for reviews](https://judge.me/help/en/articles/8379747-offering-judge-me-generated-coupon-codes-for-reviews) (Judge.me Reward Conditions): This article explains how Judge.me evaluates review submissions and media after a waiting period to determine if a customer qualifies for a reward.

### `kimonix`

Read: Yotpo catalog card. Help centre: http://help.kimonix.com/ (—); 0 articles read.

Functions:
- **Collection Merchandising and Sorting**: Uses Yotpo review and rating data as merchandising criteria to sort collections and prioritize high-converting, high-rated products.
- **Email Product Recommendations**: Generates personalized product recommendations driven by product performance and review data for inclusion in email campaigns.

Accepted: none. the help centre at http://help.kimonix.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `klaviyo`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/klaviyo-oauth-integration-yotpo-loyalty-referrals, Yotpo guide https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo, Yotpo guide https://support.yotpo.com/docs/klaviyo-integration-guide, Klaviyo help centre: How to migrate from Yotpo to Klaviyo, Klaviyo help centre: Integrating Yotpo Loyalty & Referrals with Customer Hub, Klaviyo help centre: How to import product reviews data from another platform. Help centre: https://help.klaviyo.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Flows**: Triggers automated email and SMS sequences based on Yotpo webhook events, such as points earned, rewards redeemed, tiers reached, or referrals shared and completed.
- **Segments**: Groups customers into targeted marketing audiences based on synced Yotpo attributes, such as points balances, VIP tier status, and referral engagement.
- **Custom Profile Properties**: Stores synced customer loyalty and review attributes (such as points balance, tier name, referral link, and birthday) directly on Klaviyo profiles for dynamic personalization and message rendering.
- **Web Feeds**: Connects Klaviyo to Yotpo's external JSON review endpoint to dynamically pull and display AI-curated review highlights within email templates.
- **Customer Hub**: Enables an on-site customer portal extension that uses Yotpo API credentials and synced profile properties to display points balances, VIP tiers, and in-hub reward redemptions.
- **Campaigns**: Sends one-off email and SMS broadcasts (such as loyalty program announcements or product campaigns) featuring review highlights and personalized loyalty customer data.

Accepted:
- [How to create a metric-triggered flow](https://help.klaviyo.com/hc/en-us/articles/360003057151-How-to-create-a-metric-triggered-flow) (Flows): This article explains how to create and configure an automated flow triggered by event metrics to message customers when they take specific actions.
- [How to create customer persona segments based on activity](https://help.klaviyo.com/hc/en-us/articles/360000407272-How-to-create-customer-persona-segments-based-on-activity) (Segments): This article explains how to create targeted customer persona segments based on customer engagement and purchasing activity.
- [Understanding custom profile properties](https://help.klaviyo.com/hc/en-us/articles/115000250912-Understanding-custom-profile-properties) (Custom Profile Properties): This article explains what custom properties are, how they store contact information in Klaviyo, and how to add and use them to personalize content, segment audiences, or filter flows.
- [How to add a custom web feed in an email](https://help.klaviyo.com/hc/en-us/articles/115005258768-How-to-add-a-custom-web-feed-in-an-email) (Web Feeds): This article explains how to connect and configure an external JSON or XML web feed to dynamically display external data inside Klaviyo emails.
- [How to create and send an email campaign](https://help.klaviyo.com/hc/en-us/articles/115005054847-How-to-create-and-send-an-email-campaign) (Campaigns): This article explains the fundamentals of email campaigns and provides step-by-step instructions for creating, designing, targeting, and scheduling a one-time send in Klaviyo.
- [How to create a date property-triggered flow](https://help.klaviyo.com/hc/en-us/articles/360002732652-How-to-create-a-date-property-triggered-flow) (Flows): This article explains how to configure an automated flow triggered by a date custom property stored on a profile, such as a customer's birthday or anniversary.
- [How to create a segment of VIP customers](https://help.klaviyo.com/hc/en-us/articles/115005065707-How-to-create-a-segment-of-VIP-customers) (Segments): This article explains how to define and build segments of VIP customers using purchase history and spend criteria to target top loyalty members.
- [How to set up coupons for Customer Hub](https://help.klaviyo.com/hc/en-us/articles/39273771656987-How-to-set-up-coupons-for-Customer-Hub) (Customer Hub): This article explains how to configure and display unique and static discount coupons for shoppers within the Customer Hub interface.
- [Profile properties reference](https://help.klaviyo.com/hc/en-us/articles/115005074627-Profile-properties-reference) (Custom Profile Properties): This article explains the difference between Klaviyo and custom profile properties, how they are stored and updated on profiles, and how they function in segmentation.

### `klaviyo_customer_hub`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/yotpo-loyalty-referrals-klaviyo-customer-hub, Klaviyo Customer Hub page about Yotpo https://help.klaviyo.com/hc/en-us/articles/46364536713755, Klaviyo Customer Hub help centre: How to migrate from Yotpo to Klaviyo, Klaviyo Customer Hub help centre: Integrating Yotpo Loyalty & Referrals with Customer Hub, Klaviyo Customer Hub help centre: How to import product reviews data from another platform. Help centre: https://help.klaviyo.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Customer Hub Loyalty Extensions**: Merchants configure and activate the loyalty connection under Customer Hub extension settings by entering their API Key, GUID, and Rewards Page URL.
- **'For You' Loyalty Summary**: Displays a personalized rewards summary block surfacing the shopper's real-time points balance, VIP tier status, and next reward progress.
- **Customer Hub Rewards Page**: Renders a dedicated hub view displaying available rewards, ways to earn, referral links, and redeemed or available coupons.
- **In-Hub Reward Redemption**: Executes real-time API calls to Yotpo to redeem points for reward coupon codes and automatically apply them to the shopper's cart.
- **Customer Profile Personalization**: Customer Hub reads synced profile properties (swell_point_balance, swell_vip_tier_name, swell_referral_link, swell_has_account) to show dynamic member content.
- **Customer Hub Style and Layout Customization**: Formats and presents Yotpo loyalty elements natively within Customer Hub's cohesive layout and brand styling.

Accepted:
- [How to style your Customer Hub](https://help.klaviyo.com/hc/en-us/articles/33660482389659-How-to-style-your-Customer-Hub) (Customer Hub Style and Layout Customization): Explains how to customize the styling, colors, fonts, and layout across tabs in the Customer Hub drawer to maintain a consistent brand appearance.
- [How to create content blocks for Customer Hub](https://help.klaviyo.com/hc/en-us/articles/33660517680795-How-to-create-content-blocks-for-Customer-Hub) (Customer Profile Personalization): Explains how to create Customer Hub content blocks that leverage profile data to display personalized content and integration data such as loyalty points.

### `knocommerce`

Read: Yotpo catalog card, KnoCommerce page about Yotpo https://docs.knocommerce.com/en/articles/9722856-yotpo-integration, KnoCommerce help centre: Yotpo Integration, KnoCommerce help centre: Yotpo Integration, KnoCommerce help centre: Yotpo integration. Help centre: https://docs.knocommerce.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Survey events and completion tracking**: KnoCommerce sends survey_view, survey_response, and survey_complete event triggers to Yotpo Loyalty to reward customers through custom action earning rules
- **Survey responses and questions**: KnoCommerce captures survey questions and customer responses, sending them to tag customer profiles for use in Yotpo Loyalty & Referrals

Accepted:
- [Creating your First Survey](https://docs.knocommerce.com/en/articles/5555408-creating-your-first-survey) (Survey responses and questions): Explains how to create surveys, add and edit question titles, and configure response options.
- [Question Types](https://docs.knocommerce.com/en/articles/5555530-question-types) (Survey responses and questions): Details the various question types supported in KnoCommerce and how customers provide answers to them.

### `later`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/mavrck-integration-guide. Help centre: https://help.later.com/hc/en-us (zendesk-search); 19 articles read.

Functions:
- **Influencer Content Management**: Later sends influencer-generated content from campaigns directly into Yotpo's Visual Marketing solution for display across on-site features and shoppable galleries.
- **Product Review Collection**: Later collects user-generated product reviews from creators and transfers them into Yotpo.
- **API Credential Configuration**: Later support configures the merchant's Yotpo API Key and Secret Key within Later/Mavrck to enable the data connection.

Accepted: none. the model accepted none of the 19 articles it read

### `lateshipment_com`

Read: Yotpo catalog card, LateShipment.com page about Yotpo http://www.lateshipment.com/yotpo, LateShipment.com help centre: Yotpo smsbump integration lateshipment com, LateShipment.com help centre: Yotpo loyalty integration lateshipment com. Help centre: https://support.lateshipment.com/ (pages + sitemap); 20 articles read.

Functions:
- **OneTrack**: Tracks real-time carrier shipment statuses and transit delays, then sends post-purchase events (such as LS-Shipped, LS-In-Transit Delays, LS-Delivered) to trigger Yotpo SMSBump flows.
- **OneReturn**: Manages and tracks customer returns, passing return lifecycle events (such as LS-ReturnInitiated, LS-ReturnApproved, and LS-ReturnReceived) to Yotpo SMSBump to automate transactional messages.
- **Shipping Issue and Damage Tracking**: Detects delivery delays, in-transit delays, lost packages, and damaged packages, sending corresponding custom action events to Yotpo Loyalty to award points or coupons to affected customers.
- **SMS Notifications Event Activation**: Allows merchants within LateShipment settings to select and toggle which specific shipment tracking and return events push payloads to external messaging flows.
- **Reviews and Loyalty Module Settings**: Provides the interface within LateShipment settings where merchants enable specific issue events (e.g., LS_Delivery_Delay, LS_Lost_Package) to trigger loyalty compensation.

Accepted:
- [Getting started with SMS notifications Modified on Wed, 20 Aug, 2025 at 10:19 AM](https://support.lateshipment.com/support/solutions/articles/1070000124223-getting-started-with-sms-notifications) (SMS Notifications Event Activation): Explains how to access SMS notification settings and toggle automated notifications on for specific event triggers.
- [How to Set Up OneReturn on LateShipment.com](https://support.lateshipment.com/support/solutions/articles/1070000136809-how-to-set-up-onereturn-on-lateshipment-com) (OneReturn): Explains how to set up OneReturn by connecting an eCommerce store and configuring return methods and label settings.
- [Understanding the OneTrack Dashboard](https://support.lateshipment.com/support/solutions/articles/1070000124104-understanding-the-onetrack-dashboard) (OneTrack): Explains how the OneTrack dashboard provides real-time cross-carrier tracking and predictive delivery delay insights.
- [How to approve or reject a return in your lateshipment dashboard](https://support.lateshipment.com/support/solutions/articles/1070000137606-how-to-approve-or-reject-a-return-in-your-lateshipment-dashboard) (OneReturn): Explains how merchants manage, approve, reject, or cancel customer return requests in the OneReturn dashboard.

### `lexer`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/lexer-integration-guide-for-loyalty-referrals, Yotpo guide https://support.yotpo.com/docs/lexer-integration-guide-for-reviews-5782145, Lexer page about Yotpo https://learn.lexer.io/docs/yotpo. Help centre: https://learn.lexer.io/docs (sitemap); 20 articles read.

Functions:
- **Lexer Segment**: Uses ingested Yotpo loyalty and review attributes to build targeted customer segments based on VIP tiers, point thresholds, promoter ratings, and review history.
- **Customer Profile Attributes**: Ingests and stores standardized Yotpo loyalty metrics (points, VIP tier, redemptions, referrals) and review metrics (review counts, average rating) on unified customer profiles.
- **Lexer Compare**: Analyzes and compares segments of customers based on Yotpo loyalty tiers and review behaviors to identify product purchasing trends.
- **Lexer Track**: Monitors customer cohort trends and retention over time using synchronized Yotpo loyalty and engagement data.

Accepted:
- [Segment overview](https://learn.lexer.io/docs/segment-overview) (Lexer Segment): This article explains the core capabilities of Lexer Segment and how to use the Segment Builder to search and group customers using attributes and events.
- [Customer profiles](https://learn.lexer.io/docs/customer-profiles) (Customer Profile Attributes): This article explains what customer profiles are in Lexer and how individual attributes form unified customer records.
- [Compare attributes](https://learn.lexer.io/docs/compare-attributes) (Lexer Compare): This article explains how to use Compare to analyze and contrast customer data distributions across two specific attributes.
- [Creating segments](https://learn.lexer.io/docs/creating-segments) (Lexer Segment): This article explains how to build dynamic customer segments using search criteria and attribute building blocks in the Segment Builder.
- [Compare segments](https://learn.lexer.io/docs/compare-segments) (Lexer Compare): This article explains how to select and compare multiple customer segments to identify key similarities, differences, and contrasting attribute values.
- [Lexers attributes](https://learn.lexer.io/docs/lexers-attributes) (Customer Profile Attributes): This article explains what attributes are in Lexer, how they define customer facts, and how they are categorized and utilized across the platform.
- [Track overview](https://learn.lexer.io/docs/track-overview) (Lexer Track): This article provides an overview of Lexer Track and explains how to monitor customer data changes, segment growth, and metrics over time.
- [Track tables](https://learn.lexer.io/docs/track-tables) (Lexer Track): This article explains how to configure metric tables in Track using customer segments and attributes to track metrics over time.

### `limespot`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/limespot-integration-guide, LimeSpot page about Yotpo https://support.limespot.com/en/articles/9966828-integrating-limespot-with-yotpo-loyalty-referrals, LimeSpot page about Yotpo https://support.limespot.com/en/articles/3968735-integrating-limespot-with-yotpo-reviews, LimeSpot help centre: Integrating LimeSpot with Yotpo Reviews, LimeSpot help centre: Integrating LimeSpot with Yotpo Loyalty & Referrals, LimeSpot help centre: How to Add LimeSpot Email Widget to Yotpo Campaign. Help centre: https://support.limespot.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Product Recommendation Boxes**: Displays Yotpo star ratings, review counts, and loyalty points directly on recommended product cards across storefront pages, checkout, and post-purchase flows.
- **Visual Designer Global Settings**: Configures display toggles to show or hide user ratings, reviews, and loyalty points on recommendation widgets across the website.
- **Checkout and Post-Purchase Recommendations**: Integrates Yotpo review star ratings into product recommendation cards shown on checkout, post-purchase upsell, thank you, and order status pages.
- **Extensions and Integrations Settings**: Provides the admin interface to connect and manage third-party review and loyalty app integrations.

Accepted:
- [How to Enable/Disable the Product Review Stars](https://support.limespot.com/en/articles/1443317-how-to-enable-disable-the-product-review-stars) (Visual Designer Global Settings): Explains how to enable or disable product review stars across recommendation boxes using the General options in the Visual Designer's Global Settings.
- [Designer Settings](https://support.limespot.com/en/articles/1443302-designer-settings) (Visual Designer Global Settings): Explains how to access the Designer and use Global Settings to apply universal customizations to all recommendation boxes across a store.
- [How to add LimeSpot recommendations to Shopify Checkout page](https://support.limespot.com/en/articles/9160842-how-to-add-limespot-recommendations-to-shopify-checkout-page) (Checkout and Post-Purchase Recommendations): Explains how to add LimeSpot product recommendation blocks to the Shopify checkout page using Checkout Extensibility.
- [How to Add/Remove the Recommendation Boxes](https://support.limespot.com/en/articles/1443304-how-to-add-remove-the-recommendation-boxes) (Product Recommendation Boxes): Explains how to add and remove product recommendation boxes across different store pages using both Quick Edit and the Visual Designer.

### `listrak`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak, Yotpo guide https://support.yotpo.com/docs/listrak-integration-guide-for-reviews, Listrak page about Yotpo https://help.listrak.com/en/articles/2239379-integration-guide-ratings-and-reviews, Listrak help centre: Integration Guide: Yotpo Learn more about Listrak's integration with Yotpo and how to get it set up., Listrak help centre: Integration Guide: Yotpo, Listrak help centre: Integration guide yotpo. Help centre: https://help.listrak.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Conductor Automations**: Triggers automated email messages when loyalty events occur or contacts reach milestones, such as entering a new tier or points expiring.
- **Ratings and Reviews Solution**: Stores synced star ratings and reviews, with merchant settings for review filtering, minimum star rating thresholds, and display sorting.
- **List Manager**: Houses the dedicated Master, Loyalty, and Referral lists that Yotpo populates with program members and referred customers.
- **Behavioral Solutions (Browse Abandonment, Cart Abandonment, Recommendations)**: Dynamically pulls matched product review excerpts and star ratings into triggered emails and recommendation blocks for social proof.
- **Personalization Fields**: Receives loyalty and referral contact attributes updated by Yotpo to dynamically insert points balances, tier names, and referral links into campaigns.
- **Integrations Manager**: Generates the Listrak Client ID and Client Secret mapped to the merchant's Master and Loyalty lists to authenticate the loyalty data sync.

Accepted:
- [Integration Guide: Ratings and Reviews Learn more about the process of integrating Ratings and Reviews with Listrak.](https://help.listrak.com/en/articles/2239379-integration-guide-ratings-and-reviews) (Ratings and Reviews Solution): This article explains how to integrate external ratings and reviews providers, including Yotpo, into Listrak campaigns.
- [Loyalty Automations in Listrak Conductor](https://help.listrak.com/en/articles/6909272-loyalty-automations-in-listrak-conductor) (Conductor Automations): This article explains how to set up automated Conductor campaigns that trigger when loyalty contacts reach specific milestones.
- [Listrak Email Lists & the List Manager Learn more about what Listrak uses lists for and how to use the List Manager.](https://help.listrak.com/en/articles/1509335-listrak-email-lists-the-list-manager) (List Manager): This article explains how lists function in Listrak, what they are used for, and how to create and manage dedicated lists.
- [Loyalty Solutions Setup](https://help.listrak.com/en/articles/3224801-loyalty-solutions-setup) (List Manager): This article details setting up a dedicated loyalty list in the List Manager to manage loyalty campaigns and subscribers.
- [Locating the Client Secret and ID Learn more about where to find your Client Secret and ID.](https://help.listrak.com/en/articles/1465526-locating-the-client-secret-and-id) (Integrations Manager): This article explains how to locate and copy the Listrak Client ID and Client Secret in Integrations Management to authenticate external integrations.
- [Profile Fields for Email Subscription Points In this article we will set up Profile Fields to track the source of your subscribers, as well as additio](https://help.listrak.com/en/articles/4204721-profile-fields-for-email-subscription-points) (Personalization Fields): This article explains how to set up custom profile fields in Listrak to capture contact data for segmentation and personalization.

### `loop_subscriptions`

Read: Yotpo catalog card, Loop Subscriptions page about Yotpo https://learn.loopwork.co/en/article/yotpo-loyalty-a7wgjr, Loop Subscriptions help centre: Yotpo loyalty, Loop Subscriptions help centre: Yotpo loyalty. Help centre: https://help.loopwork.co/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Customer portal loyalty drawer**: Displays loyalty rewards and point balances directly on the subscription details page in the customer portal, allowing subscribers to redeem rewards via a customizable drawer.
- **Cancellation flows**: Incorporates the dynamic {{yotpo_points}} variable onto the cancellation benefits page and allows subscribers to redeem points within cancellation reasons to prevent churn.
- **Email notifications**: Supports the {{yotpo_points}} dynamic variable inside Loop subscription email templates to display loyalty points directly in transactional emails.
- **Multilingual texts**: Localizes and translates loyalty widget text into customers' local languages within Loop's native language settings.

Accepted:
- [Multilingual texts](https://help.loopwork.co/en/articles/12731890-multilingual-texts) (Multilingual texts): This article explains how to configure and auto-translate customer portal and Loop content across different languages mapped to Shopify markets.
- [Customer email notifications](https://help.loopwork.co/en/articles/12730180-customer-email-notifications) (Email notifications): This article explains how to access, enable, and manage the automated customer email notification templates triggered by subscription lifecycle events.
- [Loyalty in cancellation flow](https://help.loopwork.co/en/articles/15920132-loyalty-in-cancellation-flow) (Cancellation flows): This article explains how to incorporate loyalty balances and conditions across cancellation flow steps, including the benefits page and cancellation reasons.
- [Customer portal widget](https://help.loopwork.co/en/articles/15595351-customer-portal-widget) (Customer portal loyalty drawer): This article explains how to configure the customer portal loyalty widget and drawer on the subscription details page to display available points and rewards.
- [Loyalty Notifications](https://help.loopwork.co/en/articles/15958177-loyalty-notifications) (Email notifications): This article explains how loyalty-triggered email notifications work and how to add loyalty variables to customer subscription email templates.

### `loudcrowd`

Read: Yotpo catalog card. Help centre: https://help.loudcrowd.com/en (—); 0 articles read.

Functions:
- **Automated Loyalty Rewards**: LoudCrowd triggers and sends loyalty point rewards to Yotpo Loyalty when customers post qualifying visual content.
- **Instagram UGC Analysis**: LoudCrowd analyzes customer visual content on Instagram to determine which posts meet criteria for Yotpo reward points.
- **Advocate Identification**: LoudCrowd identifies top brand advocates based on content creation to qualify them for Yotpo loyalty incentives.

Accepted: none. the help centre at https://help.loudcrowd.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `loyaltylion`

Read: Yotpo catalog card, LoyaltyLion help centre: Yotpo - Integration Manual Give your customers points for verified Yotpo reviews, and keep the rule running if your Yotpo keys stop working, LoyaltyLion help centre: Yotpo - Integration Manual, LoyaltyLion help centre: Yotpo integration manual. Help centre: https://help.loyaltylion.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Earning rules**: Awards loyalty points to customers when a verified buyer review is published and detected from Yotpo.
- **Rule limits**: Enforces a mandatory restriction on how often an individual customer can earn points for submitting reviews.
- **Customer matching**: Matches the reviewer details from Yotpo to an existing loyalty customer profile by email address or store customer ID.
- **Loyalty page display**: Displays the review-earning rule, title, and description to shoppers on the storefront loyalty page.
- **Program status**: Controls review processing, automatically pausing the 5-minute review collection checks when the program is paused.

Accepted:
- [Activity: Leave a review Give points for reviews, whether your review platform has a dedicated rule or needs a custom one](https://help.loyaltylion.com/en/articles/1965589-activity-leave-a-review) (Earning rules): This article explains how LoyaltyLion awards points automatically through dedicated rules when customers submit reviews on supported platforms like Yotpo.

### `magenative`

Read: Yotpo catalog card, MageNative page about Yotpo https://magenative.com/integrations/yotpo. Help centre: https://www.magenative.com/ (—); 0 articles read.

Functions:
- **In-App Purchases and Checkout**: Processes customer orders placed directly inside the mobile app so that shoppers can earn Yotpo loyalty points for their purchases.
- **Loyalty Programs & Rewards Interface**: Displays Yotpo customer rewards and loyalty point balances directly to shoppers browsing the mobile application.
- **Product Reviews Display**: Surfaces Yotpo customer reviews within the mobile app interface to build social proof and drive conversions.

Accepted: none. the help centre at https://www.magenative.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `mailchimp`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/mailchimp-integration-yotpo-loyalty-referrals, Yotpo guide https://support.yotpo.com/docs/mailchimp-integration-guide-for-reviews, Mailchimp page about Yotpo https://mailchimp.com/help/connect-disconnect-yotpo-loyalty-referrals, Mailchimp page about Yotpo https://mailchimp.com/help/connect-disconnect-yotpo, Mailchimp help centre: Connect disconnect yotpo loyalty referrals, Mailchimp help centre: Connect disconnect yotpo. Help centre: https://mailchimp.com/help (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Customer Journeys (Automations)**: Triggers automated marketing flows based on loyalty events (e.g., joining program, earning points, redeeming rewards) and review events (e.g., review request eligibility, review submitted).
- **Audience Fields (Merge Tags)**: Receives and stores 9 customer loyalty attributes (such as points balance, VIP tier, and referral link) mapped to custom contact fields.
- **Segment Builder**: Filters contacts into targeted segments using loyalty attributes (VIP tier, loyalty status, points balance) and review properties (review score, reviewed product, review status).
- **Email Campaign Builder (Content Blocks)**: Uses dynamic blocks such as 'Feature a review' and 'Request a review' to showcase customer reviews and collect feedback directly in email layouts.
- **Contact Profile Activity Feed**: Displays individual customer interaction history, including loyalty activity and review events with star ratings and product feedback.
- **Connected Stores**: Serves as the prerequisite e-commerce platform connection (Shopify, WooCommerce, BigCommerce, Magento) to which Yotpo loyalty and reviews data is associated.

Accepted:
- [Create a Marketing Automation Flow](https://mailchimp.com/help/create-customer-journey) (Customer Journeys (Automations)): This article explains how to create and configure automated marketing flows in Mailchimp.
- [About Marketing Automation Flows | Mailchimp](https://mailchimp.com/help/about-customer-journeys) (Customer Journeys (Automations)): This article explains the core concepts, structure, and terminology behind Mailchimp marketing automation flows.
- [Manage Audience and Signup Form Fields | Mailchimp](https://mailchimp.com/help/manage-audience-signup-form-fields) (Audience Fields (Merge Tags)): This article explains the available audience field types and how to add and manage custom contact fields in Mailchimp.
- [Connecting Your Online Store to Mailchimp](https://mailchimp.com/help/connect-your-online-store-to-mailchimp) (Connected Stores): This article explains how to connect supported e-commerce platforms to Mailchimp to sync store data and access e-commerce features.

### `mesa`

Read: Yotpo catalog card, MESA page about Yotpo https://docs.getmesa.com/connect/yotpo-loyalty, MESA page about Yotpo https://docs.getmesa.com/article/1238-yotpo-loyalty, MESA page about Yotpo https://docs.getmesa.com/connect/yotpo, MESA page about Yotpo https://www.getmesa.com/connect/yotpo, MESA help centre: Yotpo, MESA help centre: Yotpo Loyalty, MESA help centre: Yotpo. Help centre: https://docs.getmesa.com/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Workflow Triggers**: Listens for incoming events such as submitted reviews, updated reviews, or loyalty updates via webhook URLs to start an automation.
- **Workflow Actions**: Executes steps in an automation sequence, such as retrieving loyalty point balances or sending review requests when delivery conditions are met.
- **App Connections**: Authenticates and stores API keys, GUIDs, and secret credentials to allow MESA to communicate securely with loyalty and reviews accounts.
- **Built-in Tools and Filters**: Applies conditional logic to incoming review data, such as routing high ratings to marketing, flagging low ratings for support, or updating tags.
- **Workflow Templates**: Provides pre-built automation blueprints to immediately route feedback, such as creating Gorgias support tickets for negative reviews.

Accepted:
- [Triggers](https://docs.getmesa.com/workflow-builder/triggers) (Workflow Triggers): This article explains what triggers are and differentiates between event-based and polling triggers that initiate automated workflows.
- [Templates](https://docs.getmesa.com/templates) (Workflow Templates): This article explains how pre-built workflow templates work and how merchants can install and customize them.
- [Actions](https://docs.getmesa.com/workflow-builder/actions) (Workflow Actions): This article explains how to authenticate, configure, and set up action steps that execute tasks after a workflow trigger.
- [Connections](https://docs.getmesa.com/going-further/credentials) (App Connections): This article explains how MESA securely saves and authenticates account login credentials and connections to integrate with third-party apps.
- [Webhook](https://docs.getmesa.com/tools/webhook) (Workflow Triggers): This article explains how to use webhook URLs to trigger MESA workflows based on incoming notifications and payloads from third-party applications.
- [Paths](https://docs.getmesa.com/tools/paths) (Built-in Tools and Filters): This article explains how conditional rules and paths route automated workflows into different branches based on specific conditions.
- [Template Library](https://docs.getmesa.com/templates/template-library) (Workflow Templates): This article explains how to browse and select pre-designed automation blueprints from the Template Library to meet specific integration goals.

### `movable_ink`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/movable-ink-integration-guide, Movable Ink page about Yotpo https://exchange.movableink.com/solution/yotpo. Help centre: https://support.movableink.com/hc/en-us (zendesk-search); 0 articles read.

Functions:
- **API Data Sources**: Connects to Yotpo public API endpoints via GET requests to ingest real-time product ratings, reviews, and visual UGC using product or customer IDs.
- **Data Source Fields**: Maps and extracts specific data attributes from Yotpo API responses, such as star ratings, review counts, reviewer names, and review sentences.
- **Dynamic Content Editor**: Designs visual email creatives that bind Yotpo data source fields to display real-time UGC, ratings, and reviews dynamically at the moment of engagement.

Accepted: none. the help centre at https://support.movableink.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `nosto`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/nosto-integratio-guide-reviews-ugc, Nosto page about Yotpo https://partners.nosto.com/technologies/yotpo, Nosto help centre: How To Integrate Yotpo with Nosto, Nosto help centre: How to integrate yotpo with nosto. Help centre: https://help.nosto.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **On-Site Product Recommendations**: Displays Yotpo star ratings, review counts, and user-generated customer photos directly within recommendation slots and widgets.
- **Integrations & UGC Sync Settings**: Receives the Yotpo App Key in Nosto settings to sync published customer photos and visual UGC into Nosto's media library.
- **Product Metadata and Ratings Configuration**: Captures review count and average star rating metadata via Shopify rich snippets or Adobe Commerce rating source settings.
- **Personalized Emails**: Incorporates Nosto's dynamic product recommendation widgets into email marketing campaigns to drive conversion with social proof.
- **Behavioral Pop-ups**: Showcases authentic customer photos and reviews in on-site behavioral pop-ups to build buyer trust.

Accepted:
- [How to use UGC from Yopto, Foursixty or Olapic in Recommendations?](https://help.nosto.com/en/articles/9661197-how-to-use-ugc-from-yopto-foursixty-or-olapic-in-recommendations) (Integrations & UGC Sync Settings): Explains how to connect Yotpo to Nosto using the Yotpo App Key in account integration settings to sync user-generated photos.
- [How to use User-Generated Content (UGC) in Recommendations?](https://help.nosto.com/en/articles/1453130-how-to-use-user-generated-content-ugc-in-recommendations) (On-Site Product Recommendations): Explains the requirements and process for incorporating authentic user-generated content from third-party providers into on-site product recommendation campaigns.
- [How Personalized Emails Work](https://help.nosto.com/en/articles/598683-how-personalized-emails-work) (Personalized Emails): Explains the technical mechanics behind dynamic image rendering and real-time product updates in Nosto's personalized email widgets.
- [Adding product review ratings to your Recommendation templates](https://help.nosto.com/en/articles/586919-adding-product-review-ratings-to-your-recommendation-templates) (On-Site Product Recommendations): Explains how to display product review star ratings and review counts in recommendation templates using default template settings or custom tag fields.
- [Basics about Nosto's Behavioral Pop-ups](https://help.nosto.com/en/articles/592325-basics-about-nosto-s-behavioral-pop-ups) (Behavioral Pop-ups): Explains the concept, campaign types, and behavioral triggers used to display dynamic pop-up overlays to website visitors.
- [Getting Started With Email Personalization Widgets](https://help.nosto.com/en/articles/634622-getting-started-with-email-personalization-widgets) (Personalized Emails): Provides a step-by-step walkthrough for creating and configuring dynamic product recommendation widgets across email service providers.

### `novel`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/yotpo-loyalty-referrals-novel-integration, Novel page about Yotpo https://support.novel.com/integrations/loyalty/yotpo-1, Novel help centre: Yotpo, Novel help centre: Yotpo, Novel help centre: Yotpo. Help centre: https://support.novel.com/ (pages + llms.txt + sitemap); 17 articles read.

Functions:
- **Wallet Pass Dynamic Points Display**: Novel receives customer points balances and real-time updates from Yotpo webhooks and API sync to display live point totals directly on the Apple and Google Wallet passes.
- **Wallet Pass Tier Visuals and Tag Requirements**: Novel checks Shopify customer tags generated by Yotpo loyalty tiers to dynamically update the tier design, branding, and benefits shown on the wallet pass.
- **Welcome and Tier Upgrade Bonuses**: Novel configures custom earning rules and triggers points events in Yotpo when customers download the wallet pass or advance to a new tier.
- **Wallet Pass Referral Campaigns**: Novel embeds Yotpo referral links onto the back of the wallet pass and uses Yotpo referral webhooks to update passes and send reward notifications.
- **Push Notifications**: Novel triggers marketing, geo-targeted, and event-based mobile push notifications to passholders based on loyalty milestones, referral events, and offers.
- **Source Tags and QR Codes**: Novel generates campaign- or store-specific QR codes that create customer profiles, enroll users into Yotpo loyalty upon pass download, and track install attribution.

Accepted:
- [Source Tags](https://support.novel.com/start-guide/source-tags) (Source Tags and QR Codes): Explains how to create, schedule, and track custom install source tag links to monitor wallet pass distribution across different marketing channels.
- [Tiers](https://support.novel.com/start-guide/tiers) (Wallet Pass Tier Visuals and Tag Requirements): Explains how to set wallet pass tier requirements using real-time synced Shopify customer tags, referrals, and email lists.
- [Configure rewards](https://support.novel.com/start-guide/configure-rewards) (Welcome and Tier Upgrade Bonuses): Explains the different reward types available in Novel, including welcome bonuses for new pass installs and tier upgrade bonuses when passholders reach higher tiers.
- [Marketing pushes](https://support.novel.com/push-notifications/marketing-pushes) (Push Notifications): Explains how to compose, schedule, and send marketing push notifications segmented by tiers and customer tags.
- [Location-based pushes](https://support.novel.com/push-notifications/location-based-pushes) (Push Notifications): Explains how to configure geo-fenced push notifications triggered when customers are within 100 meters of retail locations.
- [Spend Tiers](https://support.novel.com/start-guide/tiers/spend-tiers) (Wallet Pass Tier Visuals and Tag Requirements): Explains how to map Novel tiers to Shopify customer tags so that wallet passes automatically update when customer tags change.

### `ometria`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/ometria-integration-guide-for-loyalty-referrals, Yotpo guide https://support.yotpo.com/docs/ometria-integration-guide-for-reviews, Ometria page about Yotpo https://ometria.partnerpage.io/tech-partners/yotpo, Ometria help centre: Yotpo Loyalty & Referrals: Supported events, Ometria help centre: Setting up Yotpo loyalty & referrals, Ometria help centre: Setting up Yotpo Loyalty & Referrals (legacy). Help centre: https://support.ometria.com/hc/en-gb (zendesk-search); 20 articles read.

Functions:
- **Automation campaigns**: Triggers automated customer journeys and marketing campaigns based on incoming Yotpo loyalty events such as points earned, opt-ins, and expiration reminders.
- **Customer filter and segmentation**: Uses Yotpo loyalty and review properties stored in core and custom fields to filter contacts and build segmented target audiences.
- **Custom fields and customer profiles**: Stores imported Yotpo contact data, loyalty attributes, and opt-in identifiers as custom or standard fields on Ometria contact and product records.
- **Custom events**: Receives real-time event payloads from Yotpo (such as points balance changes and expiration dates) to track loyalty activities against contacts.
- **Marketing templates and merge tags**: Populates dynamic personalization into email templates using merge tags derived from Yotpo event properties and full payload fields.
- **Connections**: Authenticates API credentials and provides webhook endpoints to ingest live loyalty and reviews data from Yotpo stores.

Accepted:
- [Automation campaign triggers](https://support.ometria.com/hc/en-gb/articles/360011316378-Automation-campaign-triggers) (Automation campaigns): It explains how entry triggers and condition logic work to initiate customer journeys in automation campaigns.
- [Segmenting contacts by custom event](https://support.ometria.com/hc/en-gb/articles/360012817658-Segmenting-contacts-by-custom-event) (Customer filter and segmentation): It explains how to use the customer filter to build segments based on custom events and their specific property types.
- [Create a custom field](https://support.ometria.com/hc/en-gb/articles/4407949072273-Create-a-custom-field) (Custom fields and customer profiles): It explains how to create and configure custom fields to store contact and order data.
- [Connections](https://support.ometria.com/hc/en-gb/articles/360012260218-Connections) (Connections): It explains how administrators can access and configure third-party application connections in Ometria.
- [Automation campaigns overview](https://support.ometria.com/hc/en-gb/articles/360011378398-Automation-campaigns-overview) (Automation campaigns): It provides an overview of how to navigate, create, and manage the statuses of automation campaigns.
- [Viewing your custom fields](https://support.ometria.com/hc/en-gb/articles/9882407677085-Viewing-your-custom-fields) (Custom fields and customer profiles): It explains how custom fields appear and are viewed within customer profiles in the single customer view.
- [Customer filter: Filtering by order and order line item custom fields](https://support.ometria.com/hc/en-gb/articles/37785901214877-Customer-filter-Filtering-by-order-and-order-line-item-custom-fields) (Customer filter and segmentation): It explains how to filter contacts and build segments using order and order line item custom fields.

### `omnisend`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/omnisend-integration-guide-for-reviews, Yotpo guide https://support.yotpo.com/docs/omnisend-integration-guide-for-yotpo-loyalty-referrals, Omnisend page about Yotpo https://support.omnisend.com/en/articles/2851596-integration-with-yotpo-product-reviews, Omnisend page about Yotpo https://support.omnisend.com/en/articles/5967363-integration-with-yotpo-loyalt, Omnisend help centre: Migrate from Yotpo to Omnisend, Omnisend help centre: Integrate Yotpo Loyalty and Referrals with Omnisend, Omnisend help centre: Integrate Yotpo Product Reviews with Omnisend. Help centre: https://support.omnisend.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Automation Workflows**: Uses Yotpo custom events as automation triggers and conditional splits to send automated email or SMS messages for reviews, point balances, rewards, and tier updates.
- **Custom Events**: Receives real-time activity data from Yotpo, including review submissions, points changes, tier status changes, and coupon awards along with their event payload fields.
- **Custom Contact Properties**: Stores customer-level loyalty and review metadata (such as latest review score, number of reviews, points balance, and VIP tier) on contact profiles.
- **Audience Segmentation**: Filters and groups contacts into segments based on Yotpo custom contact properties, such as high or low review ratings and review counts.
- **Message Personalization Tags**: Populates dynamic event properties (such as product title or review headline) directly into email and SMS copy using template tags.

Accepted:
- [Create and Manage Custom Events in Omnisend](https://support.omnisend.com/en/articles/1475482-create-and-manage-custom-events-in-omnisend) (Custom Events): Explains how custom events and event-specific custom fields are created, triggered via API or third-party integrations, and utilized in automations.
- [Collect & Manage Contact Custom Properties](https://support.omnisend.com/en/articles/1061885-collect-manage-contact-custom-properties) (Custom Contact Properties): Explains how to collect, manage, and view custom properties stored on contact profiles for personalization and segmentation.
- [Understand Omnisend Automation Trigger Settings](https://support.omnisend.com/en/articles/3947985-understand-omnisend-automation-trigger-settings) (Automation Workflows): Explains how workflow triggers and trigger filters operate to determine when and how contacts qualify to enter an automation.
- [Use Personalization in Omnisend](https://support.omnisend.com/en/articles/1061845-use-personalization-in-omnisend) (Message Personalization Tags): Explains how to add dynamic contact properties and event fields into messages across channels using personalization tags and fallback values.
- [Custom Properties and Custom Fields: Key Differences](https://support.omnisend.com/en/articles/4249357-custom-properties-and-custom-fields-key-differences) (Custom Contact Properties): Explains the differences between profile-level custom properties and event-level custom fields, including how third-party apps pass contact properties.
- [Use Liquid Templating for Message Personalization](https://support.omnisend.com/en/articles/11197418-use-liquid-templating-for-message-personalization) (Message Personalization Tags): Explains how to use Omnisend's Liquid templating syntax to dynamically personalize messages with objects, tags, and filters.
- [Set Up Automation Workflow Settings](https://support.omnisend.com/en/articles/3954813-set-up-automation-workflow-settings) (Automation Workflows): Explains how to configure, customize, and activate automation workflow settings, including triggers, audience filters, and message channels.
- [Get Started with Omnisend Segmentation](https://support.omnisend.com/en/articles/5945163-get-started-with-omnisend-segmentation) (Audience Segmentation): Explains how to build and organize audience segments based on contact profile data and subscriber behavior.

### `optimizely`

Read: Yotpo catalog card. Help centre: https://support.optimizely.com/hc/en-us (zendesk-search); 19 articles read.

Functions:
- **Customer Predictions**: Ingests loyalty and reviews data into Optimizely's data science models to calculate customer predictions and likelihood metrics.
- **Personalized Marketing Campaigns**: Uses loyalty information, review data, and data science predictions to power personalized and timely marketing campaigns.
- **Customer Profiles**: Receives and stores customer loyalty and reviews attributes to enrich unified customer profiles.

Accepted:
- [Personalized tags / Liquid Pills (Legacy) - Use liquid without writing code](https://support.optimizely.com/hc/en-us/articles/14451303190157-Personalized-tags-Liquid-Pills-Legacy-Use-liquid-without-writing-code) (Personalized Marketing Campaigns): This article explains how to insert customer and product attributes into marketing email touchpoints using personalization tags without writing code.

### `optimove`

Read: Yotpo catalog card. Help centre: https://academy.optimove.com/en (—); 0 articles read.

Functions:
- **Real-Time Campaigns**: Optimove uses incoming Yotpo loyalty events as triggers to send real-time marketing campaigns to customers.
- **Customer Profiles**: Optimove ingests streamed loyalty events to enrich individual customer profile records with loyalty behavior data.
- **Customer Segmentation**: Merchants create target groups and filter audiences based on customer profile attributes enriched with Yotpo loyalty data.
- **Real-Time Event Streaming**: Optimove receives and processes streamed loyalty event data sent in real time from Yotpo.
- **Insight Discovery**: Optimove uses enriched customer data from loyalty interactions to discover customer behavior trends and marketing insights.

Accepted: none. the help centre at https://academy.optimove.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `order_desk`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/order-desk-integration-guide, Order Desk page about Yotpo https://www.orderdesk.com/integrations/yotpo, Order Desk page about Yotpo https://help.orderdesk.com/article/690-yotpo-integration, Order Desk help centre: Yotpo Integration, Order Desk help centre: Yotpo integration. Help centre: https://help.orderdesk.com/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Auto Submit Imported Orders**: Automatically passes imported order and line item data from connected carts and marketplaces to Yotpo to trigger automatic review requests.
- **Product Code Match**: Translates cart or marketplace SKUs into matching Yotpo catalog SKUs before submitting order details to Yotpo.
- **Product Code Skip**: Filters out designated SKUs so Order Desk does not include those items when sending order data to Yotpo.
- **Rule Builder**: Automates order management workflows and conditions before or when transmitting order details to Yotpo.
- **Channel Order Import**: Consolidates and ingests order information from over 100 shopping carts and marketplaces (e.g., Amazon, eBay, Etsy, Walmart) to be forwarded to Yotpo.

Accepted:
- [How to Work with Rules](https://help.orderdesk.com/guided-walkthroughs/rules-and-automations/how-to-work-with-rules) (Rule Builder): Explains how to set up and configure automated workflows using rule types, events, and actions in the Rule Builder.
- [How to Begin Importing Orders](https://help.orderdesk.com/guided-walkthroughs/orders-and-folders/how-to-begin-importing-orders) (Channel Order Import): Explains the methods and foundational concepts for importing and ingesting orders into Order Desk through connected sales channels and integrations.
- [Rules Reference: Events, Filters and Actions](https://help.orderdesk.com/resources/rules-reference-events-filters-and-actions) (Rule Builder): Provides a comprehensive reference of all available events, filters, and actions used to trigger and execute rules in the Rule Builder.
- [Fulfillment Integration Product Settings](https://help.orderdesk.com/integration-setup-guides/fulfillment-services/fulfillment-integration-product-settings) (Product Code Match): Explains how to map shopping cart or marketplace SKUs to the expected integration SKUs before orders are submitted.

### `ordergroove`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-ordergroove. Help centre: https://docs.ordergroove.com/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Recurring order discount codes**: Ordergroove applies the loyalty discount codes redeemed by customers via Yotpo to recurring subscription orders.
- **Recurring order processing**: Ordergroove automatically processes recurring subscription orders and pushes them to the eCommerce platform, allowing Yotpo to reward subscribers with loyalty points.
- **Subscription order tagging**: Ordergroove attaches subscription order tags and attributes (such as 'Ordergroove subscription order') to orders so Yotpo can identify and reward subscription purchases.
- **API credentials management**: Ordergroove provides the account credentials needed in Yotpo's Integrations Center to establish the connection between the platforms.

Accepted:
- [Recurring Order Placement](https://docs.ordergroove.com/lifecycle/order/recurring-placement) (Recurring order processing): It explains how Ordergroove sends recurring subscription order data to the merchant's platform via API or batch methods to process and place recurring orders.
- [Authentication](https://docs.ordergroove.com/api-reference/authentication) (API credentials management): It explains how Ordergroove's Application API keys and authentication scopes work and are managed for server-to-server integrations.

### `pagefly`

Read: Yotpo catalog card. Help centre: https://help.pagefly.io/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Drag-and-Drop Page Builder**: Merchants drag and drop review widgets, star ratings, Q&A sections, and popup widgets directly into custom page layouts.
- **Third-Party App Elements**: Provides the widget element blocks within the PageFly element library to embed and automatically sync review, rating, and Q&A content.
- **Custom Pages**: Acts as the customized page templates where product reviews, ratings, and subscriber forms are rendered for customers.
- **Popup Elements**: Renders SMS subscriber collection popups on custom PageFly pages.

Accepted:
- [How to activate integrated third party Shopify apps to use on your pages](https://help.pagefly.io/integrations/third-party-elements/how-to-activate-integrated-third-party-shopify-apps-to-use-on-your-pages) (Third-Party App Elements): This article explains how to activate integrated third-party app elements from the PageFly dashboard and editor so their widgets can be added to pages.
- [How to work with PageFly editor?](https://help.pagefly.io/page-structure-and-elements/editor/user-interface/how-to-work-with-pagefly-editor) (Drag-and-Drop Page Builder): This article explains how to access, navigate, and configure the PageFly drag-and-drop editor interface to design and arrange page layouts.
- [Popup](https://help.pagefly.io/page-structure-and-elements/pagefly-elements/containers/popup) (Popup Elements): This article explains how to add, structure, and customize Popup Content container elements and overlay settings within the PageFly editor.
- [How to create a Product page with PageFly](https://help.pagefly.io/pages-and-sections-creation/pages/add-more-content-to-my-shopify-product-page) (Custom Pages): This article explains how to create and customize dedicated product page templates in PageFly to present enhanced product details.

### `plobal_apps`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/plobal-apps-integration-guide. Help centre: https://plobalapps.freshdesk.com/support (—); 0 articles read.

Functions:
- **Product Page Reviews and Ratings**: Natively displays Yotpo star ratings and reviews on mobile product pages and captures review submissions from shoppers
- **In-App Loyalty and Rewards**: Displays Yotpo point balances and earning actions, allowing customers to redeem points for reward codes directly within the mobile app
- **Mobile Checkout Discount Application**: Receives and applies discount codes generated from Yotpo Loyalty reward redemptions during in-app checkout
- **App Update and Publishing**: Pushes the mobile app update to Google Play and the Apple App Store to deploy the configured loyalty program live to shoppers

Accepted: none. the help centre at https://plobalapps.freshdesk.com/support could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `postpilot`

Read: Yotpo catalog card, PostPilot page about Yotpo https://help.postpilot.com/knowledge/integrating-with-yotpo, PostPilot help centre: Integrating with yotpo. Help centre: https://help.postpilot.com/knowledge (pages + sitemap); 20 articles read.

Functions:
- **PostPilot Flows (API Triggered)**: Receives webhook calls from Yotpo flows to trigger automated direct mail postcard sends.
- **Audience Filtering**: Uses customer membership in connected Yotpo lists and segments as criteria to include or exclude recipients.
- **MailMatch**: Matches email prospects from connected Yotpo audiences to physical home addresses for postcard delivery.
- **Audience Synchronization**: Imports and refreshes segments and lists from Yotpo SMS, Email, and Loyalty on a daily or manual schedule.
- **API Connections**: Provides API keys and destination endpoints that receive webhook payloads configured in Yotpo flows.

Accepted:
- [Api triggered segments mailmatch via api](https://help.postpilot.com/knowledge/api-triggered-segments-mailmatch-via-api) (API Connections): Explains the distinct destination endpoints provided by PostPilot's API connection for external platforms to send direct mail.
- [Creating an api connection for external use](https://help.postpilot.com/knowledge/creating-an-api-connection-for-external-use) (API Connections): Explains how to create an API connection in PostPilot and access the developer base URLs and connection tokens needed for external platform integrations.
- [Flow triggers](https://help.postpilot.com/knowledge/flow-triggers) (PostPilot Flows (API Triggered)): Explains how to select an API connection and configure webhook event sources and triggers for a PostPilot flow.
- [Setting up mailmatch segments](https://help.postpilot.com/knowledge/setting-up-mailmatch-segments) (MailMatch): Explains how PostPilot's MailMatch technology matches email prospects to physical mailing addresses and excludes existing store customers.
- [How do i use flows](https://help.postpilot.com/knowledge/how-do-i-use-flows) (PostPilot Flows (API Triggered)): Explains how to create and set up an automated flow in PostPilot that listens for webhook events to trigger direct mail sends.

### `postscript`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/postscript-integration-guide-for-yotpo-loyalty-referrals. Help centre: https://help.postscript.io/hc/en-us (zendesk-search); 0 articles read.

Functions:
- **Flows**: Triggers automated SMS messages based on synced Yotpo Loyalty events, such as points earned, redemptions, and birthdays.
- **Subscriber Segments**: Filters and groups subscribers into targeted audiences using synced loyalty customer attributes like VIP tier, points balance, and opt-in status.
- **Campaigns**: Sends one-off SMS broadcast messages targeted to audience segments built from loyalty program data.
- **Subscriber Custom Properties**: Stores customer-level loyalty attributes (such as VIP tier and opt-in status) on subscriber profiles for segmentation and message personalization.
- **API Key Management**: Generates private security key pairs in store settings to authorize data syncing from external platforms into Postscript.

Accepted: none. the help centre at https://help.postscript.io/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `powerreviews`

Read: Yotpo catalog card, PowerReviews page about Yotpo https://www.powerreviews.com/yotpo-brand-syndication. Help centre: https://www.powerreviews.com/ (—); 0 articles read.

Functions:
- **Retail Syndication Network**: Receives reviews and visual UGC collected in Yotpo to distribute and display social proof across PowerReviews retailer partner sites.
- **Product and Review Data Import**: Receives periodic uploads of product catalog feeds and review data exported from Yotpo for syndication processing.
- **Product Knowledge Graph Matching**: Matches products from incoming Yotpo review and product feeds to corresponding retailer catalog items to display UGC accurately.

Accepted: none. the help centre at https://www.powerreviews.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `productsup`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/productsup-integration-guide. Help centre: https://www.productsup.com/ (sitemap); 16 articles read.

Functions:
- **Export Channels (Exports A/B)**: Used to add and set up the export channel that structures and formats product catalog data before sending it to Yotpo.
- **Export Destinations**: Connects the export channel to Yotpo's API endpoint using your Yotpo app key and API secret to deliver the catalog feed.
- **Export Scheduling**: Automates the recurring synchronization schedule (hourly or daily) to push updated product information to Yotpo.

Accepted: none. the model accepted none of the 16 articles it read

### `reactiv`

Read: Yotpo catalog card. Help centre: https://support.reactivapp.com/en (—); 0 articles read.

Functions:
- **Reactiv Clips**: Displays Yotpo product reviews, loyalty perks, and points within short-form video clips in the mobile app.
- **In-App Product Reviews Display**: Displays ratings and customer reviews from Yotpo Reviews across product and journey pages in the mobile app.
- **In-App Loyalty and Rewards**: Displays customer points balance, perks, and earning/redemption options from Yotpo Loyalty in the mobile app.

Accepted: none. the help centre at https://support.reactivapp.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `reamaze`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/reamaze-integration-guide, Re:amaze page about Yotpo https://www.reamaze.com/integrations/yotpo, Re:amaze help centre: Yotpo Integration: Setup and Features, Re:amaze help centre: Yotpo how to. Help centre: https://support.reamaze.com/ (pages + sitemap); 19 articles read.

Functions:
- **Conversation Right Rail**: Displays Yotpo customer review count, product reviews, average rating, sentiment analysis, loyalty points balance, points earned, redemptions, and VIP tier next to active customer conversations.
- **Conversation Tags**: Enables agents to proactively tag conversations based on the customer's average ratings and sentiment retrieved from Yotpo.
- **Brand Management**: Allows multi-brand accounts to link and scope Yotpo customer review and loyalty data to a specific Re:amaze brand.

Accepted:
- [Multi-Brand](https://support.reamaze.com/kb/account-settings/managing-your-brands) (Brand Management): Explains how multi-brand works in Re:amaze and how to add and manage distinct brands with separate settings and channels within a single account.
- [Tags (Labels, Folders, Filters)](https://support.reamaze.com/kb/advanced-settings/understanding-tags-also-known-as-folders-or-labels) (Conversation Tags): Explains what tags are, how to create and manage them, and how to apply them to conversations to organize and flag customer inquiries.

### `rebuy`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/rebuy-integration-guide-for-yotpo-loyalty-referrals, Rebuy page about Yotpo https://help.rebuyengine.com/en/articles/6399623-adding-yotpo-product-reviews-to-rebuy-widgets, Rebuy page about Yotpo https://help.rebuyengine.com/en/articles/8648790-yotpo-loyalty-smart-cart-app, Rebuy help centre: Yotpo Loyalty Smart Cart™ App, Rebuy help centre: Yotpo SMS Smart Cart™ App, Rebuy help centre: Yotpo Reviews and Rebuy. Help centre: https://help.rebuyengine.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Smart Cart Apps**: Embeds loyalty point balances, customer login prompts, point-earning calculations, and SMS opt-in capture forms directly inside the Smart Cart drawer.
- **Recommendation Widgets**: Displays star ratings and review snippets alongside cross-sell, upsell, and post-purchase product recommendations.
- **Data Source Rules**: Filters and targets widget recommendations based on customer tags synced for VIP tier loyalty status.
- **Rebuy Theme Manager**: Controls the visual styling and star colors for reviews displayed within Rebuy widgets to match store branding.
- **Smart Links**: Generates dynamic cart-building URLs that can be inserted into SMS marketing messages and journeys to drive personalized conversions.

Accepted:
- [Smart Cart™ Apps](https://help.rebuyengine.com/en/articles/6593888-smart-cart-apps) (Smart Cart Apps): This article explains how Rebuy Smart Cart Apps allow partner applications to embed and display functionality directly inside the Smart Cart drawer.
- [Manage Rebuy Theme](https://help.rebuyengine.com/en/articles/8922305-manage-rebuy-theme) (Rebuy Theme Manager): This article explains how to access and configure Rebuy themes to control global branding and visual styling across widgets.
- [Using Rebuy's Smart Links](https://help.rebuyengine.com/en/articles/6197419-using-rebuy-s-smart-links) (Smart Links): This article explains how Rebuy Smart Links work to generate custom campaign URLs that guide customers to personalized shopping experiences.
- [How to Target Specific Customer Segments Using Customer Tag Rules](https://help.rebuyengine.com/en/articles/6526958-how-to-target-specific-customer-segments-using-customer-tag-rules) (Data Source Rules): This article explains how to set up Data Source rules based on customer tags to target personalized widget recommendations to specific customer segments.
- [Data Sources 101](https://help.rebuyengine.com/en/articles/8871643-data-sources-101) (Data Source Rules): This article explains the core IF/RETURN structure and sequential evaluation logic that Data Sources use to determine which products surface in widgets.

### `recharge`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/recharge-integration-guide-for-yotpo-loyalty-referrals, Recharge help centre: Migrate from Yotpo to Recharge, Recharge help centre: Supported apps and integrations. Help centre: https://support.getrecharge.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Subscription discount codes**: Yotpo Loyalty & Referrals generates coupon codes that apply to Recharge products or ongoing recurring subscriptions.
- **Shopify order and customer tags**: Recharge automatically creates order and customer tags for subscription events and renewals, which Yotpo uses to trigger earning rules and assign loyalty tiers.
- **Recharge App Marketplace**: Merchants access the Recharge Marketplace under Tools & apps to find and initiate the connection with Yotpo.

Accepted:
- [Managing subscription discount codes](https://support.getrecharge.com/hc/en-us/articles/360034748173-Managing-subscription-discount-codes) (Subscription discount codes): This article explains how to create, import, and apply discount codes to recurring subscription purchases across different checkout integrations.
- [Using Shopify order and customer tags](https://support.getrecharge.com/hc/en-us/articles/360008829873-Using-Shopify-order-and-customer-tags) (Shopify order and customer tags): This article explains how Recharge automatically assigns customer and order tags in Shopify based on subscription activity and subscriber status.
- [Applying and removing a discount from an existing subscription](https://support.getrecharge.com/hc/en-us/articles/360008683234-Applying-and-removing-a-discount-from-an-existing-subscription) (Subscription discount codes): This article explains how to apply, manage, and remove discount codes on existing customer subscriptions and recurring charge queues.

### `refersion`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/refersion-integration-guide-for-yotpo-loyalty-referrals, Refersion page about Yotpo https://support.refersion.com/en/articles/4393854-yotpo-loyalty-referrals-integration, Refersion help centre: Yotpo Loyalty & Referrals Integration, Refersion help centre: Yotpo Loyalty & Referrals Integration, Refersion help centre: Yotpo loyalty referrals integration. Help centre: https://support.refersion.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Affiliate application approval**: Approving a pending affiliate application in Refersion triggers the event that sends the completed custom action into Yotpo to award loyalty points to the customer.
- **Affiliate registration page**: Provides the affiliate sign-up URL that is linked within Yotpo's custom action campaign tile so loyalty members can register for the affiliate program.
- **URL fields population**: Pre-populates fields on the affiliate registration form using URL parameters to ensure the applicant's email matches their Yotpo customer account.

Accepted:
- [Customize & Promote Your Affiliate Registration Page](http://support.refersion.com/en/articles/2952798-customize-promote-your-affiliate-registration-page) (Affiliate registration page): This article explains how to access and customize the affiliate registration form, including its branding, content, and form fields.
- [How Do I Automatically Approve Affiliate Applications?](http://support.refersion.com/en/articles/1906618-how-do-i-automatically-approve-affiliate-applications) (Affiliate application approval): This article explains how to automatically approve affiliate applications submitted to specific offers.
- [Affiliates Page Overview](http://support.refersion.com/en/articles/6630136-affiliates-page-overview) (Affiliate application approval): This article explains how to review pending affiliate applications and approve or deny them individually or in bulk.
- [How To Find Your Refersion Subdomain and API Keys](http://support.refersion.com/en/articles/1064045-how-to-find-your-refersion-subdomain-and-api-keys) (Affiliate registration page): This article explains where to find your Refersion subdomain and the direct URL to your affiliate registration page.

### `remarkety`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/remarkety-integration-guide, Remarkety page about Yotpo https://www.remarkety.com/blog/yotpo-reviews, Remarkety help centre: Integrate Yotpo and Remarkety, Remarkety help centre: Segmenting Customers - The Complete Filter Guide. Help centre: https://support.remarkety.com/hc/en-us (zendesk-search); 19 articles read.

Functions:
- **Product Recommendation Blocks**: Embeds dynamic product recommendations in emails populated with Yotpo star ratings, review counts, and top review text.
- **Order and Cart Items Blocks**: Displays products from an active cart or past order alongside Yotpo average scores, star images, and top reviews.
- **Dynamic Template Tags**: Uses Remarkety template logic and formatting filters to conditionally display Yotpo star ratings, review counts, and quoted review titles in custom templates.
- **Automated Email Campaigns**: Automated flows such as browse abandonment and abandoned cart recovery leverage synced Yotpo reviews to add social proof to triggered messages.
- **Connected Apps Settings**: Merchants authorize and manage the connection within Remarkety settings to trigger initial and real-time syncing of product review data.

Accepted:
- [Types of Product Recommendations](https://support.remarkety.com/hc/en-us/articles/208150186-Types-of-Product-Recommendations) (Product Recommendation Blocks): This article explains the different recommendation algorithms available in Remarkety and how to use them to predict products for shoppers in email campaigns.

### `retention_science`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-retention-science, Retention Science help centre: Connect Swell with ReSci. Help centre: https://help.retentionscience.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Cortex HTML Email Editor and Merge Tags**: Merchants select and insert Yotpo Loyalty merge tags (such as point balance, referral link, and tier name) directly into email templates to personalize email content.
- **Customer Profile Attributes**: Receives and stores synced loyalty and referral data (e.g., points balance, referral code, VIP tier, affiliate status) as user attributes that update automatically.
- **Cortex Automated Email Campaigns**: Enables merchants to create automated, AI-driven emails targeted to customers based on their loyalty and referral status.
- **ReSci Integration Center**: Provides the interface to install the Swell plugin and generate the API key needed to authenticate and sync data with Yotpo Loyalty.

Accepted:
- [Advanced merge tags and conditional statements](https://help.retentionscience.com/hc/en-us/articles/115003287847-Advanced-merge-tags-and-conditional-statements) (Cortex HTML Email Editor and Merge Tags): This article explains how to use dynamic merge tags and conditional Liquid statements within email templates to display personalized user content.
- [How To Create New Emails](https://help.retentionscience.com/hc/en-us/articles/227181648-How-To-Create-New-Emails) (Cortex Automated Email Campaigns): This article walks through the process of creating a new stage-based Cortex email, including configuring sender details, subject lines, filters, and settings.
- [About the Integration Center](https://help.retentionscience.com/hc/en-us/articles/360015418473-About-the-Integration-Center) (ReSci Integration Center): This article provides an overview of navigating the Integration Center to browse, install, and manage third-party integrations and generate API keys.
- [Merge tag overview: All available tags and how to use them](https://help.retentionscience.com/hc/en-us/articles/215162088-Merge-tag-overview-All-available-tags-and-how-to-use-them) (Cortex HTML Email Editor and Merge Tags): This article explains how merge tags function in email templates to dynamically insert individual user profile attributes and dynamic content.
- [Setting Up Cortex Stages](https://help.retentionscience.com/hc/en-us/articles/115008000827-Setting-Up-Cortex-Stages) (Cortex Automated Email Campaigns): This article explains how Cortex stages operate to automate customer communications and how to navigate stage tiles to set up email templates.

### `rule`

Read: Yotpo catalog card, Rule page about Yotpo https://en.docs.rule.se/article/449-integrera-yotpo-loyalty-rewards-med-rule, Rule help centre: Yotpo Loyalty, Rule help centre: Yotpo – Ställ in automationer, Rule help centre: Yotpo loyalty. Help centre: https://help.rule.io/sv (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Automations**: Executes automated workflows triggered when specific Yotpo event tags (e.g., ReferralCompleted, TierEarned, Birthday) are assigned to contacts.
- **Tags**: Receives Yotpo event identifiers as contact tags that classify subscribers and initiate automated flows.
- **Custom Subscriber Fields**: Stores customer loyalty data sent from Yotpo, including points balances, tier status, spend totals, and referral links.
- **Email Templates**: Uses mapped Yotpo subscriber fields as dynamic placeholders to display reward codes, referral URLs, and tier details in emails.
- **SMS Messaging**: Sends automated SMS messages, such as birthday congratulations or reward alerts, triggered by Yotpo loyalty events.
- **Date-based Triggers**: Runs recurring annual automations triggered by customer birthday or anniversary dates captured via Yotpo.

Accepted:
- [Medlemsfält](https://help.rule.io/sv/articles/348454-medlemsfalt) (Custom Subscriber Fields): Explains how custom member fields and field groups work, including supported data types and API naming conventions.
- [Hur skapar man en tagg?](https://help.rule.io/sv/articles/348650-hur-skapar-man-en-tagg) (Tags): Provides step-by-step instructions on how to create and manage tags to categorize contacts.
- [Redigera mall i klassiska editorn](https://help.rule.io/sv/articles/348903-redigera-mall-i-klassiska-editorn) (Email Templates): Explains how to edit email templates in the editor and insert dynamic elements such as member fields.
- [Skapa en automation](https://help.rule.io/sv/articles/348499-skapa-en-automation) (Automations): Explains how to create automated workflows triggered by tags or segments to send email and SMS messages.
- [Taggar & Segment](https://help.rule.io/sv/articles/348644-taggar-segment) (Tags): Explains what tags represent in Rule, how they differ from segments, and how to exclude tagged lists from sends.
- [Exempel på automationer](https://help.rule.io/sv/articles/348500-exempel-pa-automationer) (Date-based Triggers): Details how to configure automated flows triggered by date member fields, including recurring annual settings for birthdays.
- [SMS i Journey Builder](https://help.rule.io/sv/articles/349428-sms-i-journey-builder) (SMS Messaging): Explains how to add and configure automated SMS messages within customer journey flows.

### `rush`

Read: Yotpo catalog card. Help centre: https://support.rush.app/ (pages); 3 articles read.

Functions:
- **Shipment Tracking and Delivery Statuses**: Rush tracks shipment and delivery progress to provide accurate, real-time order delivery information to Yotpo for timely review requests
- **Order Tracking Event Triggers**: Rush generates order milestone and tracking events to update customer communication workflows with up-to-date order information

Accepted:
- [Shipments](https://support.rush.app/shipments/about/general.html) (Shipment Tracking and Delivery Statuses): It explains how the Shipments section organizes and tracks orders across different transit stages and delivery statuses.

### `salesforce_commerce_cloud`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/salesforce-commerce-cloud-installing-yotpo-reviews, Salesforce Commerce Cloud page about Yotpo https://www.salesforce.com/products/commerce-cloud/partner-marketplace/partners/yotpo-quick-launch-solution. Help centre: https://help.salesforce.com/ (—); 0 articles read.

Functions:
- **Cartridge Management**: Used to deploy and register the official Yotpo cartridge in the B2C Commerce cartridge path to enable backend connection and frontend logic.
- **Storefront Templates and Components**: Serves as the frontend presentation layer where Yotpo widgets, Q&A, and Visual UGC components are embedded and rendered.
- **Backend Connection and Web Services**: Establishes the backend communication channel between the Salesforce Commerce Cloud store and Yotpo servers.

Accepted: none. the help centre at https://help.salesforce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `salesforce_marketing_cloud`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-salesforce-marketing-cloud. Help centre: https://help.salesforce.com/ (—); 0 articles read.

Functions:
- **Data Extensions**: Receives and stores synced Yotpo events and customer loyalty attributes such as point balances and referral links in the SwellCustomerAttributes table.
- **Contact Builder**: Links the SwellCustomerAttributes Data Extension to Contact Data via Email Address to map loyalty data to contact profiles.
- **Personalization Strings**: References synced Yotpo customer attributes (e.g., swell_point_balance, swell_referral_link) to dynamically populate email content.
- **Journey Builder**: Enables marketers to target and trigger automated customer journeys based on loyalty program engagement and status.
- **Installed Packages**: Hosts the package installed from AppExchange to facilitate data exchange with the external loyalty platform.
- **Business Units**: Defines the account workspace within Marketing Cloud, scoped to the single business unit supported by the data sync.

Accepted: none. the help centre at https://help.salesforce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `searchanise`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/searchanise-integration-guide, Searchanise help centre: Yotpo integration magento1. Help centre: https://docs.searchanise.io/ (pages + sitemap); 19 articles read.

Functions:
- **Instant Search Widget**: Searchanise displays Yotpo star ratings and reviews directly on product items within the instant search dropdown as users type.
- **Search Results Page**: Searchanise displays Yotpo ratings and review counts on product cards across the dedicated search results page.
- **Force Re-indexation**: Searchanise uses catalog re-indexation to sync Yotpo review data, running automatically every 24 hours or triggered manually by the merchant for immediate updates.

Accepted:
- [Product reviews bigcommerce](https://docs.searchanise.io/product-reviews-bigcommerce) (Force Re-indexation): Explains that Searchanise automatically syncs product reviews every 24 hours and describes how to trigger Force re-indexation manually to update review ratings immediately.
- [Indexing shopify](https://docs.searchanise.io/indexing-shopify) (Force Re-indexation): Explains how Searchanise catalog indexation works, when merchants need to trigger re-indexation (including after importing reviews), and how to run manual or scheduled updates.

### `searchspring`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/searchspring-integration-guide, Searchspring help centre: Yotpo Integration, Searchspring help centre: External Authorizations, Searchspring help centre: Data Feed Guide. Help centre: https://help.searchspring.net/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Facets and Filtering**: Searchspring uses product review scores ingested from Yotpo to populate facet filters, allowing shoppers to filter search and category results by rating.
- **Sorting**: Searchspring uses Yotpo review score data as a sorting attribute, enabling shoppers to sort product results by rating.
- **Product Badging**: Searchspring utilizes Yotpo review scores to display visual badges and rating indicators on product cards in search and listing results.
- **External Authorizations**: Searchspring Management Console tool where merchants connect and authorize their store sites to import ratings data via OAuth.
- **Merchandising Rules and Product Arrangement**: Searchspring enables merchants to arrange products on search, category, and landing pages manually or via automated rules based on product attributes like ratings.

Accepted:
- [Sort Options](https://help.searchspring.net/hc/en-us/articles/206986683-Sort-Options) (Sorting): This article explains how to configure and add custom sorting options based on product data fields within the Searchspring Management Console.
- [Badge Manager](https://help.searchspring.net/hc/en-us/articles/25177004340123-Badge-Manager) (Product Badging): This article explains how merchants can design, position, and configure condition-based rules for product badges on product cards.
- [External Authorizations](https://help.searchspring.net/hc/en-us/articles/52660160291227-External-Authorizations) (External Authorizations): This article explains how to access the External Authorizations tool in the Searchspring Management Console to connect external platforms, including Yotpo.
- [How Products are Arranged on Search Result Pages](https://help.searchspring.net/hc/en-us/articles/360003060691-How-Products-are-Arranged-on-Search-Result-Pages) (Merchandising Rules and Product Arrangement): This article explains the hierarchy and priority order of rules and shopper selections that dictate how products are arranged on search result pages.
- [Boosting Rules](https://help.searchspring.net/hc/en-us/articles/115000298686-Boosting-Rules) (Merchandising Rules and Product Arrangement): This article explains how to set up dynamic product boosting rules based on product attributes within Visual Merchandising campaigns.

### `shogun`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/shogun-integration-guide, Shogun page about Yotpo https://getshogun.com/help/en/articles/2689995-how-do-i-display-reviews-on-my-shopify-pages, Shogun page about Yotpo https://getshogun.com/help/en/articles/3977880-yotpo-product-reviews-for-bigcommerce. Help centre: https://getshogun.com/help/en (—); 0 articles read.

Functions:
- **Product Reviews Element**: Displays Yotpo star ratings or review widgets on the page, with controls for review counts, character limits, styling colors, and typography.
- **Product Box Element**: Acts as the container that binds the page to a specific product and variant, providing the product context required to render Yotpo reviews.
- **HTML Element**: Enables manual embedding of Yotpo's Star Rating or Reviews Widget code by replacing dynamic Liquid tags with static product attributes.
- **Integrations Settings**: Houses the connection configuration in the Shogun dashboard where the Yotpo app key is entered and saved.

Accepted: none. the help centre at https://getshogun.com/help/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `shopify`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20. Help centre: https://help.shopify.com/en/manual (pages + sitemap); 0 articles read.

Functions:
- **Theme app embeds**: Merchants enable the Loyalty app embed and script loaders in the Shopify theme editor so loyalty and rewards widgets render on the storefront.
- **Customer accounts**: Shopify handles customer account creation, login links, and authentication (legacy or new customer accounts), which customers use to interact with the loyalty program.
- **App installation and permissions**: Merchants install and authorize the app via the Shopify App Store to connect the Shopify store to Yotpo.

Accepted: none. 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles

### `shopify_flow`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/creating-loyalty-referrals-workflows-in-shopify-flow, Yotpo guide https://support.yotpo.com/docs/creating-yotpo-workflows-in-shopify-flow. Help centre: https://help.shopify.com/en/manual (pages + sitemap); 0 articles read.

Functions:
- **App triggers**: Shopify Flow receives event data when a review is created or updated in Yotpo to start automated workflows.
- **App actions**: Shopify Flow triggers the Yotpo Loyalty & Referrals 'Reward Points' action, sending customer email, action name, campaign type, and point values.
- **Workflow conditions**: Filters workflows by checking Yotpo review attributes (star rating, published status, title, content) or customer attributes (tags, segments) before running actions.
- **Template variables**: Allows merchants to dynamically pass trigger data, such as {{customer.email}}, into action fields for customer identification.
- **Shopify native triggers**: Captures native store events, such as customer email marketing subscriptions, to kick off points-earning loyalty workflows.
- **Workflow testing and activation**: Enables previewing and turning on automated workflows so review and loyalty triggers run in the store.

Accepted: none. 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles

### `shopify_plus`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20, Yotpo guide https://support.yotpo.com/docs/shopify-installing-yotpo-reviews-on-online-store-20, Shopify Plus page about Yotpo https://www.shopify.com/partners/blog/beyond-the-build-yotpo. Help centre: https://help.shopify.com/en/manual (pages + sitemap); 0 articles read.

Functions:
- **Theme App Embeds**: Loads and executes required Yotpo scripts, module loaders, and SDKs globally across the storefront via Shopify's theme editor.
- **Theme App Blocks**: Places and configures UI components like the Reviews Widget and Star Rating within Online Store 2.0 sections and template layouts.
- **Customer Accounts**: Provides customer authentication, login links, and account version management (Legacy vs. New customer accounts) needed for loyalty program participation.
- **Product Catalog**: Maintains product records and pushes catalog updates to Yotpo to ensure review requests and displayed ratings match store inventory.

Accepted: none. 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles

### `shopify_point_of_sale`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-loyalty-and-referrals-with-shopify-point-of-sale-pos, Yotpo guide https://support.yotpo.com/docs/shopify-point-of-sale-pos-integration-for-reviews. Help centre: https://help.shopify.com/en/manual (pages + sitemap); 5 articles read.

Functions:
- **Shopify POS Smart Grid App Tiles**: Merchants add the Yotpo Loyalty & Rewards POS UI extension as a tile on the POS smart grid to allow store staff to access loyalty actions during transactions.
- **Shopify POS Cart Discounts**: Receives and applies redeemed loyalty discounts to the POS cart while enforcing discount combinations, minimum spend, and product-specific restrictions.
- **Shopify POS Customer Metafields**: Displays pinned loyalty customer metafields directly within customer profiles on the POS interface for store staff to reference.
- **Shopify POS Order and Customer Data Capture**: Captures customer details (name and email) and order data (order ID, product ID, fulfillment status) at checkout to pass to Yotpo for review requests and loyalty points.

Accepted: none. 15 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles

### `shoppinggives`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/integrating-donations-with-loyalty-referrals-shoppinggives. Help centre: https://faq.shoppinggives.com/hc/en-us (zendesk-search); 0 articles read.

Functions:
- **Point-to-Donation Redemptions**: Processes charity donations generated when customers exchange their loyalty reward points for a donation amount rather than a store discount
- **Purchase Donation Tracking**: Tracks and reports charitable donation amounts generated on purchases so Yotpo can award loyalty points per dollar donated
- **Donation Tax Receipts**: Manages tax receipting compliance, ensuring appropriate tax credit allocation when donations originate from redeemed loyalty points
- **Change Commerce App Activation**: Provides the foundational store setup and widget configuration required for collecting and routing donations

Accepted: none. the help centre at https://faq.shoppinggives.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `siena`

Read: Yotpo catalog card. Help centre: https://support.siena.cx/hc/en-us (zendesk-search); 0 articles read.

Functions:
- **AI Automated Responses**: Siena references Yotpo Loyalty data to automatically answer customer inquiries about their loyalty accounts and rewards
- **Onsite Chat**: Provides the onsite conversational interface where shoppers interact with AI to dynamically receive their loyalty information
- **Dynamic Customer Context**: Receives customer loyalty information from Yotpo to ground AI conversations in real-time customer data

Accepted: none. the help centre at https://support.siena.cx/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `smile_io`

Read: Yotpo catalog card, Smile.io page about Yotpo https://help.smile.io/en/articles/4036202-yotpo-and-smile, Smile.io page about Yotpo https://blog.smile.io/smile-app-yotpo, Smile.io help centre: Yotpo integration overview, Smile.io help centre: Yotpo integration setup, Smile.io help centre: Overview. Help centre: https://help.smile.io/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Ways to Earn Points**: Merchants configure a review earning rule in Smile to set the point value, title, and instructions awarded when customers submit verified product reviews via Yotpo.
- **Earning Limits**: Smile uses earning limit rules to restrict how often or how many times a customer can earn points for submitting reviews.
- **Customer Points Ledger**: Smile awards points directly to the customer's account and logs review reward activity when verified reviews are submitted through Yotpo.

Accepted:
- [Configure ways to earn points](https://help.smile.io/en/articles/4036267-configure-ways-to-earn-points) (Ways to Earn Points): This article explains how to create, configure point values for, and edit earning actions in Smile.
- [Configure points earning limits](https://help.smile.io/en/articles/4036269-configure-points-earning-limits) (Earning Limits): This article explains how to set time-based limits on earning actions to restrict how frequently customers can earn points.
- [View program activity](https://help.smile.io/en/articles/14021875-view-program-activity) (Customer Points Ledger): This article explains how to monitor individual points events and view earning activity logged on customer profiles.
- [Customize the name of a way to earn](https://help.smile.io/en/articles/10603965-customize-the-name-of-a-way-to-earn) (Ways to Earn Points): This article explains how to customize the customer-facing name of an earning action.

### `social_nature`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/social-nature-integration-guide. Help centre: https://socialnaturehelp.zendesk.com/hc/en-us (zendesk-search); 9 articles read.

Functions:
- **Review syndication**: Social Nature automatically exports and syndicates collected consumer ratings and reviews to the merchant's review store using API credentials.
- **Post-trial review collection**: Social Nature collects ratings and reviews from consumers following product trial and sampling campaigns to send to Yotpo.
- **Seeding disclaimers and metadata**: Social Nature configures and transmits custom disclaimer text and metadata fields alongside reviews to identify them as product seeding trials.

Accepted: none. the model accepted none of the 9 articles it read

### `sopost`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/sopost-integration-guide. Help centre: https://help.sopost.com/en (pages); 9 articles read.

Functions:
- **Ratings and Reviews Syndication**: Sends collected post-trial review data (review title, review text, and star rating) from SoPost sampling campaigns to Yotpo products
- **Integration Settings Key Management**: Stores Yotpo API credentials (app key and API secret) within SoPost settings to authenticate review syndication
- **Sampling Campaign Setup**: Configures campaign review collection forms and maps Yotpo product IDs to ensure syndicated reviews match catalog products
- **Post-Trial Review Collection**: Collects consumer feedback fields (title, text, star rating) after product trials that qualify for syndication

Accepted:
- [SoPost Feedback Options](http://help.sopost.com/en/articles/9027869-sopost-feedback-options) (Post-Trial Review Collection): Explains SoPost's review feedback collection option, including the standard fields like star rating, review title, and review text that can be syndicated to Yotpo.

### `stitch`

Read: Yotpo catalog card, Stitch page about Yotpo https://www.stitchdata.com/integrations/yotpo, Stitch page about Yotpo https://www.stitchdata.com/integrations/yotpo/mode, Stitch page about Yotpo https://www.stitchdata.com/docs/integrations/saas/yotpo, Stitch help centre: Yotpo. Help centre: https://www.stitchdata.com/docs (pages); 20 articles read.

Functions:
- **Destinations**: Receives and stores replicated Yotpo data in central warehouses or data lakes such as Snowflake, Google BigQuery, Amazon Redshift, or Amazon S3.
- **Table and Column Selection**: Allows users to choose which specific Yotpo tables, attributes, and columns Stitch replicates to the destination warehouse.
- **Replication Scheduling**: Sets how often Stitch queries Yotpo to sync data using sync frequency, anchor scheduling, or cron settings.
- **Replication Methods and Keys**: Determines whether Yotpo data is extracted via key-based incremental replication or full table replication, tracking replication keys to detect updates.
- **Progress Monitoring and Logs**: Provides visibility into the status of Yotpo sync runs through extraction logs, progress summaries, and destination loading reports.
- **Loading Behavior and Schema Management**: Controls how Stitch maps incoming Yotpo data types, structures the destination schema, and loads rows into the warehouse.

Accepted:
- [Selecting tables and columns](https://www.stitchdata.com/docs/replication/extractions/data-selection/setting-tables-and-columns-to-replicate) (Table and Column Selection): Explains how to select and deselect specific tables and columns to replicate from an integration into the destination warehouse.
- [Overview](https://www.stitchdata.com/docs/destinations) (Destinations): Explains Stitch's destination architecture and how destinations receive and store replicated data from source integrations.
- [Replication Frequency](https://www.stitchdata.com/docs/replication/replication-scheduling/replication-frequency) (Replication Scheduling): Explains how to configure replication frequency to control how often Stitch extracts and syncs data from an integration.
- [Key-based Incremental](https://www.stitchdata.com/docs/replication/replication-methods/key-based-incremental) (Replication Methods and Keys): Explains how key-based incremental replication utilizes replication keys to identify and sync new and updated records.
- [Extraction Logs](https://www.stitchdata.com/docs/replication/extractions/integration-extraction-logs) (Progress Monitoring and Logs): Explains how to access and interpret extraction logs to monitor integration sync runs and identify extraction details.
- [Understanding loading behavior](https://www.stitchdata.com/docs/replication/loading/understanding-loading-behavior) (Loading Behavior and Schema Management): Explains how Stitch handles schema changes, maps incoming data types, and writes records into destination tables.
- [System tables and columns](https://www.stitchdata.com/docs/replication/loading/system-tables-columns) (Loading Behavior and Schema Management): Explains the system metadata columns and tables Stitch automatically generates in destination schemas to track replicated records.
- [Loading Reports](https://www.stitchdata.com/docs/replication/integration-loading-reports) (Progress Monitoring and Logs): Explains how to view and evaluate destination loading reports to monitor the status and volume of loaded data.
- [Replicating new and additional columns](https://www.stitchdata.com/docs/replication/syncing-new-additional-columns) (Table and Column Selection): Explains how to add and replicate new or previously unselected columns on existing synced tables.
- [Full Table](https://www.stitchdata.com/docs/replication/replication-methods/full-table) (Replication Methods and Keys): Explains how full table replication extracts and replicates the entire contents of a table during each replication run.
- [Advanced Scheduling using Cron](https://www.stitchdata.com/docs/replication/replication-scheduling/advanced-scheduling) (Replication Scheduling): Explains how to schedule replication syncs at specific times and custom intervals using cron expressions.
- [Choosing a destination](https://www.stitchdata.com/docs/destinations/choosing-a-stitch-destination) (Destinations): Explains key considerations and technical requirements when choosing and configuring a destination data warehouse or data lake.

### `subtotal`

Read: Yotpo catalog card, Subtotal page about Yotpo https://subtotal.com/docs/integrations/yotpo. Help centre: https://subtotal.com/docs (pages); 8 articles read.

Functions:
- **Action Configuration**: Maps Subtotal events to Yotpo Custom Actions, sets retailer filters, and configures point calculation rules and start dates.
- **Purchase Data Collection (purchase.created)**: Tracks collected retail purchases, computes points based on item subtotal spend, and sends the reward event to Yotpo.
- **Account Linking (account.linked)**: Triggers an event when a customer links a retailer account via Subtotal Link to award Yotpo points.
- **Customer Connection Management**: Captures customer emails, customer IDs, and mobile numbers across connections to match customer profiles in Yotpo.

Accepted:
- [Concepts](https://subtotal.com/docs/concepts) (Purchase Data Collection (purchase.created)): This article explains how Subtotal continuously syncs and evaluates retail purchases from connected accounts, including the transaction totals and item metadata it collects.

### `talkable`

Read: Yotpo catalog card, Talkable page about Yotpo https://docs.talkable.com/email_marketing_and_automation/yotpo, Talkable help centre: Yotpo, Talkable help centre: Yotpo, Talkable help centre: Yotpo. Help centre: https://docs.talkable.com/ (pages + llms.txt + sitemap); 19 articles read.

Functions:
- **Person Custom Properties**: Receives and stores real-time Yotpo loyalty metrics including point balances, VIP tier names, redemptions, and referral stats on customer profiles.
- **Incentive Criteria**: Evaluates Yotpo custom properties (like VIP tier status) using Liquid logic in campaign rules to grant exclusive or tiered advocate referral rewards.
- **Talkable Wallet**: Displays synchronized Yotpo loyalty points balances alongside referral rewards in the Apple Wallet pass header configured via the campaign editor.
- **People Report**: Displays individual customer details and synced Yotpo custom properties to track loyalty-driven referral performance.
- **App Store**: Provides the OAuth installation interface to connect credentials, authorize access, and activate real-time loyalty data syncing.

Accepted:
- [Incentive Criteria](https://docs.talkable.com/campaigns/tutorials/incentive_criteria) (Incentive Criteria): Explains how to configure incentive trigger conditions evaluated with Liquid logic to determine when rewards are issued.
- [Pass Custom User Data](https://docs.talkable.com/advanced_features/passing_custom_data) (Person Custom Properties): Explains how custom properties are structured as key-value pairs to store user data that can be evaluated in criteria and rendered in campaign views.
- [Talkable Wallet](https://docs.talkable.com/wallet) (Talkable Wallet): Explains the core features of Talkable Wallet passes, including displaying reward details and loyalty points balances on customer mobile devices.
- [Configuring Talkable Wallet](https://docs.talkable.com/wallet/configuration) (Talkable Wallet): Explains how to configure and customize wallet pass fields in the campaign editor using Liquid templates and custom data.

### `tapcart`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/tapcart-yotpo-integration-guide, Tapcart page about Yotpo https://help.tapcart.com/en/articles/12261042-yotpo-loyalty-integration. Help centre: https://help.tapcart.com/en (pages); 1 articles read.

Functions:
- **App Studio (Loyalty Screens and Blocks)**: Displays Yotpo loyalty tier progress, available points, rewards list, and point redemption ledger across custom loyalty screens.
- **Product Detail Page (PDP) Reviews and UGC**: Renders Yotpo star ratings, customer reviews, review collection forms, and visual UGC product galleries directly on Tapcart PDPs.
- **Cart and Checkout Redemption**: Applies Yotpo point redemptions, fixed/percentage discounts, free shipping, and free product rewards directly to the shopper's cart.
- **Push Notifications and App Download Events**: Triggers Yotpo custom action earning rules to award loyalty points when users download the app or opt in to push notifications.
- **Homepage Shoppable Media Galleries**: Displays Yotpo Visual UGC shoppable image albums and banners directly on the mobile app homepage.
- **Account Hub**: Serves as the shopper entry point linking directly to the Yotpo Loyalty Center and member rewards summary.

Accepted: none. the model accepted none of the 1 articles it read

### `teamwork_commerce`

Read: Yotpo catalog card. Help centre: https://www.teamworkcommerce.com/ (—); 0 articles read.

Functions:
- **POS Customer Loyalty Lookup**: Displays customer loyalty details, including points balances, VIP status, and available rewards directly on the register screen.
- **POS Reward Redemption**: Allows cashiers to redeem and apply live Yotpo customer rewards directly to the order during checkout.
- **In-Store Sales Processing**: Transmits completed store purchase data to Yotpo to automatically calculate and award loyalty points to customers.
- **Returns and Refunds Processing**: Sends return and refund records to Yotpo so points earned from returned items can be automatically deducted or adjusted.

Accepted: none. the help centre at https://www.teamworkcommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `tiktok_shop`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/tiktok-shop-yotpo-reviews-integration. Help centre: https://partner.tiktokshop.com/doc (—); 0 articles read.

Functions:
- **Product Rating Import**: Merchants access Product Rating in Seller Center to initiate the review import process and link external reviews to products.
- **Product Identifier Codes (GTIN/UPC/EAN)**: TikTok Shop uses product identifier codes assigned to SKUs to match incoming reviews to the correct catalog products.
- **Product Detail Page Reviews Module**: Displays imported product reviews with source attribution alongside native reviews on the TikTok Shop product page.
- **Batch Product Catalog Update (CSV)**: Merchants export and re-import product catalog CSV files in Seller Center to bulk update product identifier codes needed for review matching.
- **TikTok Shop App Store Authorization**: Merchants install and authorize the connector app within the TikTok Shop App Store to grant data access.
- **TikTok Shop Products API**: Merchants use the API to programmatically edit SKU product identifier codes to align catalog data for review syndication.

Accepted: none. the help centre at https://partner.tiktokshop.com/doc could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `tray_io`

Read: Yotpo catalog card. Help centre: https://tray.ai/ (llms.txt + sitemap); 14 articles read.

Functions:
- **Workflows**: Allows merchants to build automated processes and logic flows that process and route Yotpo event and customer data across other platforms.
- **Connectors**: Connects third-party applications across the technology stack to send and receive data to and from Yotpo.
- **Webhook Trigger**: Listens for real-time events sent from external apps to trigger Tray.io automation workflows.

Accepted: none. the model accepted none of the 14 articles it read

### `treet`

Read: Yotpo catalog card, Treet help centre: Issuing Seller Credit Via Your Yotpo Loyalty Program . Help centre: https://treetbrandsuccess.zendesk.com/hc/en-us (zendesk-search); 10 articles read.

Functions:
- **Seller Payout Options**: Treet presents loyalty points alongside cash as a payout method for sold items and triggers point deposits via Yotpo when selected
- **Item Listing Estimation**: Treet calculates and displays the estimated loyalty points a customer will earn when quoting earnings during the item listing process
- **Payout Confirmation Emails**: Treet sends an automated notification email to peer sellers confirming that loyalty points have been deposited into their account

Accepted: none. the model accepted none of the 10 articles it read

### `vajro`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/vajro-integration-guide, Vajro help centre: How to enable Yotpo Product Reviews & Photos, Vajro help centre: How to enable yotpo product reviews photos. Help centre: https://docs.vajro.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Mobile app product reviews display**: Yotpo supplies product reviews, photo reviews, video reviews, and average star ratings to display natively on iOS and Android product pages.
- **Mobile app Q&A**: Yotpo supplies question and answer content to display natively on product pages within the mobile app.
- **Plugins manager**: Vajro's dashboard section where merchants input credentials to enable and manage product review features across their mobile app.

Accepted: none. the model accepted none of the 20 articles it read

### `viralsweep`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/viralsweep-integration-guide, ViralSweep page about Yotpo https://www.viralsweep.com/blog/increase-product-reviews-with-yotpo-and-viralsweep, ViralSweep page about Yotpo https://www.viralsweep.com/integrations/yotpo, ViralSweep help centre: Yotpo, ViralSweep help centre: Yotpo, ViralSweep help centre: Yotpo. Help centre: https://support.viralsweep.com/ (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Social Actions (Post-Entry Actions)**: Provides the post-entry action framework where merchants add and configure the review task, customize the action title, and connect the product to be reviewed.
- **Bonus Entries**: Tracks review completion and automatically awards the designated number of sweepstakes or contest entries to entrants who submit a review.
- **Review Action Form**: Displays an in-widget form to campaign participants to collect star ratings and review text, then transmits the review data to Yotpo via API.
- **Product Selector**: Pulls and displays the store's product list from Yotpo via API credentials, allowing merchants to select a target product for the review campaign.

Accepted:
- [Social Actions](https://support.viralsweep.com/en/articles/9272775-social-actions) (Social Actions (Post-Entry Actions)): This article explains how ViralSweep's social actions work to incentivize participants and award additional promotion entries upon completing designated tasks.

### `virtue`

Read: Yotpo catalog card, Virtue page about Yotpo https://www.virtueimpact.com/post/virtue-x-yotpo-turn-loyalty-points-into-lasting-impact, Virtue page about Yotpo https://help.virtueimpact.com/en/articles/11583309-virtue-x-yotpo-rewards, Virtue help centre: Virtue X Yotpo Rewards, Virtue help centre: Virtue x yotpo rewards. Help centre: https://help.virtueimpact.com/en (pages + llms.txt + sitemap); 20 articles read.

Functions:
- **Store Giving (Give from Sales of Specific Products)**: Maps the Shopify donation product redeemed via Yotpo Free Product rewards to a chosen cause and allocates 100% of the product value as the donation amount.
- **Customer Giving**: Creates the Shopify donation product and on-site donation widgets so shoppers can donate at checkout, which Yotpo tracks via Points for Purchase rules to grant loyalty points.
- **Virtue Payouts Screen**: Tracks cumulative donations and provides an order-level breakdown of contributions triggered by Yotpo reward redemptions and customer giving.
- **Cause Directory and Custom Causes**: Allows merchants to select from 60,000+ verified charities or add custom nonprofit partners to receive donations generated from redeemed loyalty points.
- **Post-Purchase Widget**: Displays the donation amount generated from the completed order, confirming the impact of points redeemed or customer donations made at checkout.
- **Impact Calculator**: Displays the collective store impact and total donation milestones achieved across all orders, including points-funded donations.

Accepted:
- [Donations and your Loyalty Program](https://help.virtueimpact.com/en/articles/11514826-donations-and-your-loyalty-program) (Store Giving (Give from Sales of Specific Products)): Explains how to create a donation product and configure Store Giving from specific products to donate 100% of the product value when redeemed through a loyalty program.
- [Give from specific products/collections](https://help.virtueimpact.com/en/articles/8510055-give-from-specific-products-collections) (Store Giving (Give from Sales of Specific Products)): Explains how to select specific products, configure donation amounts, and assign unique causes for product-level giving.
- [How does customer giving work?](https://help.virtueimpact.com/en/articles/8329792-how-does-customer-giving-work) (Customer Giving): Explains how Virtue automatically creates and manages the catalog donation product and its cause variants to add customer donations to the cart.
- [Viewing payouts and donations](https://help.virtueimpact.com/en/articles/9946630-viewing-payouts-and-donations) (Virtue Payouts Screen): Explains how to access the payouts page to track monthly giving and view itemized donation records contributing to each payout.
- [Impact calculator](https://help.virtueimpact.com/en/articles/8264203-impact-calculator) (Impact Calculator): Explains how the Impact Calculator widget showcases storewide giving totals and calculated impact across active causes, along with setup steps.
- [Allowing customers to make donations](https://help.virtueimpact.com/en/articles/8263172-allowing-customers-to-make-donations) (Customer Giving): Explains how to enable customer giving, configure preset donation amounts, and deploy donation widgets across the customer journey.
- [How to find causes](https://help.virtueimpact.com/en/articles/8263516-how-to-find-causes) (Cause Directory and Custom Causes): Explains how to search, filter by tag, and select partner charities from Virtue's directory of verified causes.
- [Adding your own cause - Detailed Instructions](https://help.virtueimpact.com/en/articles/8263543-adding-your-own-cause-detailed-instructions) (Cause Directory and Custom Causes): Explains the process for adding custom nonprofit partners to Virtue by providing cause details, branding assets, and compliance documentation.

### `weglot`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/weglot-integration-guide. Help centre: https://support.weglot.com/ (pages + sitemap); 20 articles read.

Functions:
- **Dynamic Content Translation**: Detects and translates dynamic text and asynchronous elements rendered by Yotpo widgets, galleries, and loyalty modules.
- **Translation Exclusions**: Allows merchants to exclude specific blocks, URLs, or paragraphs from translation to keep select Yotpo content in its original language.
- **Iframe Translation**: Translates embedded content when Yotpo widgets or tools are rendered inside iframes on the storefront.
- **Translation Management and Customization**: Allows merchants to view, customize, and edit the translated strings generated for Yotpo reviews, galleries, and loyalty features.
- **Language Switcher Customization**: Controls the appearance and behavior of the button customers use on the storefront to switch languages and trigger translated Yotpo modules.

Accepted:
- [How to translate dynamic content?](https://support.weglot.com/article/253-how-to-translate-dynamic-content) (Dynamic Content Translation): Explains how to identify dynamic elements with browser developer tools and configure dynamic translation rules in Weglot to translate content updated in real-time.
- [How can I exclude URLs, blocks, or words from translation?](https://support.weglot.com/article/95-how-to-exclude-urls-blocks-words-from-translation) (Translation Exclusions): Explains how to set up URL, block, and word exclusions in the Weglot dashboard to prevent specified content from being translated.
- [How to edit my translations](https://support.weglot.com/article/128-how-to-edit-my-translations) (Translation Management and Customization): Explains how to view, manage, and manually edit automatic translations within the Weglot Translations List.
- [How to change the design of the language switcher?](https://support.weglot.com/article/281-how-to-change-the-design-of-the-language-switcher) (Language Switcher Customization): Explains how to customize the appearance, design options, language names, and flags of the Weglot language switcher.
- [How can I create translation rules?](https://support.weglot.com/article/130-translations-exceptions) (Translation Exclusions): Explains how to define translation exception rules in the Glossary to ensure specific words or phrases are never translated.
- [How to use the visual editor](https://support.weglot.com/article/409-how-to-use-the-visual-editor) (Translation Management and Customization): Explains how to use the Visual Editor to locate and edit translated strings directly on an interactive preview of the storefront.
- [How to use the Switcher Editor?](https://support.weglot.com/article/349-how-to-use-the-switcher-editor) (Language Switcher Customization): Explains how to adjust the position and placement of the language switcher on the storefront using the interactive Switcher Editor.

### `wonderment`

Read: Yotpo catalog card. Help centre: https://docs.wonderment.com/ (—); 0 articles read.

Functions:
- **Shipping Related Communications**: Wonderment supplies shipment data and triggers to automate and personalize customer shipping communications
- **Custom Tracking URLs**: Wonderment generates unique custom tracking links that are dynamically included in shipping communications
- **Estimated Arrival Time Properties**: Wonderment calculates and provides estimated arrival dates and custom shipment properties for delivery messaging

Accepted: none. the help centre at https://docs.wonderment.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `woocommerce`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/woocommerce-installing-yotpo, WooCommerce page about Yotpo https://woocommerce.com/products/yotpo-social-reviews. Help centre: https://woocommerce.com/ (—); 0 articles read.

Functions:
- **Order Status Management**: WooCommerce order status updates (such as 'Completed') trigger sending order details to Yotpo to schedule automatic review request emails.
- **Product Reviews Settings**: The storewide product reviews setting in WooCommerce must be enabled to activate review capabilities across the storefront.
- **Product Comment and Review Controls**: WooCommerce's per-product comment settings dictate whether the reviews widget can render on individual product pages, managed individually or via bulk edit.
- **Product Reviews Data Export**: Existing WooCommerce customer reviews and ratings are exported from the store to be imported into Yotpo.

Accepted: none. the help centre at https://woocommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

### `yieldify`

Read: Yotpo catalog card. Help centre: https://support.yieldify.com/en (pages); 20 articles read.

Functions:
- **Website Personalization Engine**: Displays and amplifies Yotpo customer reviews, loyalty incentives, and SMS promotions through personalized on-site messaging and experiences.

Accepted:
- [Dynamic Content How to create highly targeted and relevant on-site experiences that speak directly to each visitor.](http://support.yieldify.com/en/articles/11478574-dynamic-content) (Website Personalization Engine): This article explains how to dynamically insert personalized content, variables, and conditional messages into on-site campaigns based on visitor behavior and data.
- [Yieldify Experiences by Type Understand the different types of Experiences you can build with Yieldify](http://support.yieldify.com/en/articles/9173278-yieldify-experiences-by-type) (Website Personalization Engine): This article explains the different types of website experiences available in Yieldify—including core enhancements, promotional experiences, and lead capture—to drive conversions and personalize the visitor journey.

### `zendesk`

Read: Yotpo catalog card, Yotpo guide https://support.yotpo.com/docs/zendesk-integration-guide-for-reviews. Help centre: https://support.zendesk.com/hc/en-us (zendesk-search); 20 articles read.

Functions:
- **Solved ticket status**: Zendesk marks tickets as solved, which triggers Yotpo to send Mail After Service review requests to customers who received support.
- **Ticket management and agent replies**: Support agents receive and respond to customer reviews and questions as tickets directly within the Zendesk agent interface.
- **Zendesk Multibrand**: Merchants configure multiple brand subdomains in Zendesk so individual Yotpo stores can link to their corresponding brand.

Accepted:
- [Updating and solving tickets](https://support.zendesk.com/hc/en-us/articles/4408832151834-Updating-and-solving-tickets) (Ticket management and agent replies): This article explains how support agents update tickets with public replies and internal notes and change status in the Zendesk agent interface.
- [About the ticket lifecycle and ticket statuses](https://support.zendesk.com/hc/en-us/articles/8263915942938-About-the-ticket-lifecycle-and-ticket-statuses) (Solved ticket status): This article explains the ticket lifecycle and standard ticket statuses in Zendesk, including how tickets transition to solved and closed states.
- [Setting up multiple brands](https://support.zendesk.com/hc/en-us/articles/4408829476378-Setting-up-multiple-brands) (Zendesk Multibrand): This article explains how multiple brands work in Zendesk and how to configure and manage branded support channels and tickets.

## Needs a person: the help centre could not be read automatically (39)

- `adscale`: help centre https://help.adscale.com/en blocks automated reading (bot check); a person picks the articles
- `alloy_automation`: the articles at https://runalloy.com/ show no text without a browser; a person picks the articles
- `amasty`: help centre https://amasty.com/docs blocks automated reading (bot check); a person picks the articles
- `antavo`: the help centre at https://antavo.atlassian.net/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `bigcommerce`: the help centre at https://support.bigcommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `daitafix`: the help centre at https://daitafix.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `dialogue`: the help centre at https://help.nowdialogue.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `digioh`: the help centre at https://help.digioh.com/knowledgebase could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `drip`: help centre https://www.drip.com/learn/docs blocks automated reading (bot check); a person picks the articles
- `ecocart`: the help centre at https://support.ecocart.io/knowledge could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `emarsys`: the help centre at https://help.emarsys.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `fast_simon`: the help centre at https://www.fastsimon.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `findify`: the help centre at https://developers.findify.io/docs could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `fomo`: the help centre at https://fomo.family/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `kimonix`: the help centre at http://help.kimonix.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `klevu`: help centre https://help.klevu.com/support blocks automated reading (bot check); a person picks the articles
- `loudcrowd`: the help centre at https://help.loudcrowd.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `magenative`: the help centre at https://www.magenative.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `movable_ink`: the help centre at https://support.movableink.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `optimove`: the help centre at https://academy.optimove.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `plobal_apps`: the help centre at https://plobalapps.freshdesk.com/support could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `postscript`: the help centre at https://help.postscript.io/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `powerreviews`: the help centre at https://www.powerreviews.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `reactiv`: the help centre at https://support.reactivapp.com/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `rise_ai`: help centre https://help.rise.ai/en blocks automated reading (bot check); a person picks the articles
- `salesforce_commerce_cloud`: the help centre at https://help.salesforce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `salesforce_marketing_cloud`: the help centre at https://help.salesforce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `shogun`: the help centre at https://getshogun.com/help/en could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `shopify`: 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles
- `shopify_flow`: 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles
- `shopify_plus`: 20 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles
- `shopify_point_of_sale`: 15 of 20 articles at https://help.shopify.com/en/manual refused automated reading (bot check); a person picks the articles
- `shoppinggives`: the help centre at https://faq.shoppinggives.com/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `siena`: the help centre at https://support.siena.cx/hc/en-us could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `teamwork_commerce`: the help centre at https://www.teamworkcommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `tiktok_shop`: the help centre at https://partner.tiktokshop.com/doc could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `triple_whale`: help centre https://kb.triplewhale.com/en blocks automated reading (bot check); a person picks the articles
- `wonderment`: the help centre at https://docs.wonderment.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks
- `woocommerce`: the help centre at https://woocommerce.com/ could not be searched or listed (it may need a login, have moved, or need a browser); a person picks

## No help centre found (37)

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

## Help centre read, nothing accepted (13)

- `adobe_commerce_magento`: the model accepted none of the 14 articles it read
- `bazaarvoice`: the model accepted none of the 14 articles it read
- `bhn_rewards`: the model accepted none of the 6 articles it read
- `braze`: the model accepted none of the 15 articles it read
- `builder_io`: the model accepted none of the 2 articles it read
- `glew`: the model accepted none of the 20 articles it read
- `later`: the model accepted none of the 19 articles it read
- `productsup`: the model accepted none of the 16 articles it read
- `social_nature`: the model accepted none of the 9 articles it read
- `tapcart`: the model accepted none of the 1 articles it read
- `tray_io`: the model accepted none of the 14 articles it read
- `treet`: the model accepted none of the 10 articles it read
- `vajro`: the model accepted none of the 20 articles it read

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

## Links proposed for two integrations (kept on the first) (2)

- https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20: `shopify`, also `shopify_plus`
- https://support.yotpo.com/docs/social-push: `facebook`, also `twitter`

## Already in the knowledge base (17)

- https://support.yotpo.com/docs/integrating-yotpo-reviews-with-attentive (in `attentive`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-attentive (in `attentive`)
- https://docs.pushowl.com/en/articles/14075206-yotpo-reviews-integration (in `brevo_pushowl`)
- https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital (in `dotdigital`)
- https://marketing.help.dotdigital.com/en/articles/8199355-easyeditor-extensions-app-blocks-overview (in `dotdigital`)
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
