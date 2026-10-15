# Messaging platforms: sources for C0.4

Prepared for Leo, 2026-10-13. This lists, for each of the 13 email and SMS platforms in roadmap
C0.4, the Yotpo or partner integration guide and 1–3 of the platform's own help pages on how its
journeys or flows work: triggers, re-entry, delays, and which conditions are checked again at send
time. Every link was opened on 2026-10-13.

- **status**: `ok` means the page loaded (HTTP 200, right title). `redirect` means the old link
  forwards to a new address; use the new one. `dead` means it does not load. `bot-check` means
  the page exists (confirmed through the help centre's own article API), but the site shows a
  "Just a moment…" bot check to automated fetches. The crawler will probably be blocked there, so
  expect to paste these.
- **approval**: every row is `candidate` until you approve it.
- `…/` in the roadmap table means `https://support.yotpo.com/docs/`.

---

## Braze

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/braze-integration-guide | yotpo guide | ok | "Braze - Integration Guide" | candidate |
| https://www.braze.com/docs/user_guide/messaging/canvas/create_a_canvas | mechanics | ok (old `engagement_tools/...` path redirects here) | Canvas entry types (scheduled, action-based, API), entry audience, re-eligibility window | candidate |
| https://www.braze.com/docs/user_guide/messaging/canvas/canvas_components/delay_step | mechanics | ok (old path redirects) | Delay step: durations, what happens to users already waiting when a delay is edited | candidate |
| https://www.braze.com/docs/user_guide/messaging/canvas/canvas_components/audience_paths | mechanics | ok | Audience is checked when the user reaches the step, not at entry; profile can change during later delays | candidate |

## Cordial

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-cordial | yotpo guide | ok | "Integrating Yotpo Loyalty & Referrals with Cordial" | candidate |
| https://support.cordial.com/hc/en-us/articles/360015822851-Podium-Orchestrations | mechanics | bot-check | Cordial's journey tool ("Podium Orchestrations"): triggers, Wait Until steps, trigger frequency limits | candidate |
| https://support.cordial.com/hc/en-us/articles/115005364367-Triggered-automated-messages | mechanics | bot-check (old slug "Automated-Messages-Sending-Methods" also works) | Event-triggered messages: delays, and whether later triggers during a delay send again or are ignored | candidate |

## Drip

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/drip-integration-guide | yotpo guide | ok | "Drip - Integration Guide" (Reviews) | candidate |
| https://help.drip.com/hc/en-us/articles/4424702655501-Workflows-Triggers | mechanics | bot-check | Workflow triggers; a person cannot enter a workflow they are already in | candidate |
| https://help.drip.com/hc/en-us/articles/4424702654221-Workflows-Exits | mechanics | bot-check | Exits, and re-entering after an exit when the trigger happens again | candidate |

## HubSpot

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/hubspot-integration-guide-for-reviews | yotpo guide | ok | "HubSpot - Integration Guide for Reviews" | candidate |
| https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-hubspot | yotpo guide | ok | "Integrating Yotpo Loyalty & Referrals with HubSpot" | candidate |
| https://knowledge.hubspot.com/workflows/set-event-enrollment-triggers | mechanics | ok | Event-based enrollment triggers for workflows | candidate |
| https://knowledge.hubspot.com/workflows/add-re-enrollment-triggers-to-a-workflow | mechanics | ok | Re-enrollment is off by default; how it works when turned on | candidate |
| https://knowledge.hubspot.com/workflows/manage-workflow-enrollment-settings | mechanics | ok | Enrollment settings, including unenrollment when records stop meeting criteria | candidate |

## Insider

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://academy.insiderone.com/docs/external-platform-integrations-yotpo | partner guide | redirect (from `academy.useinsider.com/...`) | Title "Yotpo"; Insider is now "Insider One" | candidate |
| https://academy.insiderone.com/docs/send-yotpo-data-to-insider-one | partner guide | redirect (from `academy.useinsider.com/docs/sending-yotpo-data-to-insider`) | "Send Yotpo Data to Insider One". This is on Insider's site, **not** support.yotpo.com (`support.yotpo.com/docs/sending-yotpo-data-to-insider` is a 404) | candidate |
| https://academy.insiderone.com/docs/wait-for-event | mechanics | ok | Architect (Insider's journey builder): Wait for Event, timeouts, matching the entry event's values | candidate |
| https://academy.insiderone.com/docs/architect-activation-status-and-time | mechanics | ok | Journey statuses, what happens to users mid-journey when it is stopped | candidate |

## Mailchimp

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/mailchimp-integration-guide-for-reviews | yotpo guide | ok | "Mailchimp - Integration Guide for Reviews" | candidate |
| https://support.yotpo.com/docs/mailchimp-integration-yotpo-loyalty-referrals | yotpo guide | ok | "Mailchimp - Integration Guide for Yotpo Loyalty & Referrals" | candidate |
| https://mailchimp.com/help/about-customer-journeys/ | mechanics | ok | Now titled "About Marketing Automation Flows" (Customer Journeys was renamed): starting points, rules, time delays, re-entry setting | candidate |
| https://mailchimp.com/help/edit-customer-journey-map/ | mechanics | ok | "Edit a Marketing Automation Flow": pausing, and what happens to contacts in a delay while paused | candidate |

## Optimizely (Zaius)

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://apps.zaius.com/yotpo-swel | partner guide | **dead** (404) | The roadmap link has a typo | — |
| https://apps.zaius.com/yotpo-swell | partner guide | ok | "Yotpo Swell" on the old Zaius apps site; says the app does not import Reviews | candidate |
| https://docs.optimizely.com/data-platform/docs/integrate-yotpo-swell | partner guide | ok | **Better replacement.** "Integrate Yotpo Swell - ODP documentation" (Loyalty) | candidate |
| https://docs.optimizely.com/data-platform/docs/integrate-yotpo-ratings-reviews | partner guide | ok (support.optimizely.com link redirects here) | "Integrate Yotpo Ratings & Reviews": a separate app, covers the Reviews side | candidate |
| https://docs.optimizely.com/data-platform/docs/configure-campaign-enrollment | mechanics | ok | Campaign enrollment: event-triggered (behavioral) campaigns, rules re-checked before each touchpoint, per-hour caps | candidate |
| https://docs.optimizely.com/data-platform/docs/legacy-understand-campaign-configuration-basics | mechanics | ok | Delays between touchpoints, send time. The URL says "legacy" | candidate |

## Optimove

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/optimove-integration-guide-for-yotpo-loyalty-referrals | yotpo guide | ok | "Optimove - Integration Guide for Yotpo Loyalty & Referrals" | candidate |
| https://academy.optimove.com/hc/en-us/articles/8717995904285-How-to-Build-a-Stream | mechanics | bot-check | Streams (Optimove's journeys): Wait Until Day, Wait for Event split, daily recurrence | candidate |
| https://academy.optimove.com/hc/en-us/articles/8698273488541-Understanding-Campaign-Duration | mechanics | bot-check | Campaign duration, which controls how often one customer can be targeted again | candidate |
| https://developer.optimove.com/docs/triggered-campaigns-1 | mechanics | ok | Triggered (real-time event) campaigns, developer view | candidate |

## Remarkety

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/remarkety-integration-guide-for-reviews | yotpo guide | redirect (from `.../remarkety-integration-guide`) | "Remarkety - Integration Guide for Reviews" | candidate |
| https://support.remarkety.com/hc/en-us/articles/7427449223188-Getting-Started-with-Journeys | mechanics | bot-check | Journeys: triggers with filters, Wait, If/Else split steps | candidate |

Only one mechanics page found. Remarkety's help centre has little on re-entry or send-time checks.

## Retention Science

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-retention-science | yotpo guide | ok | "Integrating Yotpo Loyalty & Referrals with Retention Science" | candidate |
| https://help.retentionscience.com/hc/en-us/articles/360015174573-Connect-Swell-with-ReSci | partner guide | bot-check | ReSci's own Swell/Yotpo setup article (last edited 2021) | candidate |
| https://help.retentionscience.com/hc/en-us/articles/204800567-Trigger-Happy-React-to-Every-Customer-Action | mechanics | bot-check | Triggered campaigns on customer actions in Cortex, ReSci's AI send engine (last edited 2021) | candidate |
| https://help.retentionscience.com/hc/en-us/articles/215994507-Users-Are-Getting-Messages-Too-Frequently | mechanics | bot-check | Time between sends is set by ReSci's model; how to take more control (last edited 2021) | candidate |

## Rule

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://help.rule.io/en/articles/349490-yotpo-loyalty | partner guide | redirect (from `en.docs.rule.se/article/449-integrera-yotpo-loyalty-rewards-med-rule`) | "Yotpo Loyalty", now **in English** (updated 2025-11-06); lists the Yotpo events sent to Rule as tags | candidate |
| https://help.rule.io/en/articles/348499-create-an-automation | mechanics | ok | Automations triggered by a tag or segment, with per-message delays | candidate |
| https://help.rule.io/en/articles/348562-faq-automations | mechanics | ok | Automation FAQ: what counts as a trigger; API-added subscribers trigger, mass imports do not | candidate |
| https://help.rule.io/en/articles/349424-troubleshooting-my-journey-is-not-being-sent | mechanics | ok | Journey Builder: why a send did not happen (segment and filter settings) | candidate |

## Sailthru

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-sailthru | yotpo guide | ok | "Integrating Yotpo Loyalty & Referrals with Sailthru" | candidate |
| https://products.zetaglobal.com/sailthru/Content/integrations/swell-2/swell-2.html | partner guide | ok | "Swell Integration": Sailthru's own page for the Yotpo Loyalty connection | candidate |
| https://products.zetaglobal.com/sailthru/Content/lo/overview/flow-builder.html | mechanics | ok | Lifecycle Optimizer flow builder, incl. re-entry settings (allow multiple, block while active, time limit) | candidate |
| https://products.zetaglobal.com/sailthru/Content/lo/lo-step-glossary/entries.html | mechanics | ok | Entry types; some entries run as a nightly job, and Wait is used to hold sends to a time of day | candidate |
| https://products.zetaglobal.com/sailthru/Content/lo/lo-step-glossary/checks.html | mechanics | ok | Check steps (conditions evaluated when the user reaches them) | candidate |

The old Sailthru docs at `getstarted.sailthru.com` did not respond. `getstarted.meetmarigold.com` forwards to a Zeta Global redirect page, and `products.zetaglobal.com/sailthru/...` is the live address.

## Salesforce Marketing Cloud

| link | kind | status | note | approval |
|---|---|---|---|---|
| https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-salesforce-marketing-cloud | yotpo guide | ok | "Integrating Yotpo Loyalty & Referrals with Salesforce Marketing Cloud" | candidate |
| https://help.salesforce.com/s/articleView?id=mc_jb_choose_a_contact_entry_mode.htm&language=en_US&type=5 | mechanics | ok (JavaScript page) | Journey Builder re-entry modes: no re-entry, any time, only after exiting | candidate |
| https://help.salesforce.com/s/articleView?id=mc_jb_wait_activity.htm&language=en_US&type=5 | mechanics | ok (JavaScript page) | Wait activities: by duration or attribute, daily goal and exit checks while waiting | candidate |
| https://help.salesforce.com/s/articleView?language=en_US&id=mc_jb_entry_events.htm&type=0 | mechanics | ok (JavaScript page) | Entry sources: API events and contact events | candidate |

---

## Flags for Leo

1. **Optimizely (Zaius): the roadmap link is broken.** `apps.zaius.com/yotpo-swel` is missing an
   "l". The fixed address works, but Optimizely now has a better page for the same app on its own
   documentation site (listed above). The Loyalty app says plainly that it **does not bring in
   Reviews**. Reviews is a separate Optimizely app with its own guide, which is also listed. The
   catalog shows this platform as Loyalty and Reviews, so the two need different guides.
2. **Insider: one link pointed at the wrong site.** "Sending Yotpo data to Insider" is on
   Insider's help site, not Yotpo's. The Yotpo address returns "page not found". Insider has also
   renamed itself "Insider One" and moved its help site. Both old links forward to the new
   addresses.
3. **Rule: the guide is no longer in Swedish.** The old Swedish link now forwards to an English
   article on Rule's new help site (updated November 2025). Use the new address.
4. **Sailthru now lives under Zeta Global.** Its old help sites don't load, or forward to a Zeta
   page. The live documentation is on Zeta's site. Sailthru also has its own page for the Yotpo
   Loyalty connection, listed above.
5. **Retention Science looks stale.** Its website is still up, but its help articles were mostly
   last edited in 2021. Third-party listings say the company was bought (one names Constant
   Contact). I could not confirm that from an official source. Consider asking whether Yotpo
   still supports this integration before adding it.
6. **Expect to paste some pages by hand.** Cordial, Drip, Optimove (Academy), Remarkety and
   Retention Science show a "checking your browser" screen to automated visitors, so the crawler
   will probably fail on them. Salesforce's help pages build their text in the browser, so a crawl
   may come back nearly empty. Paste those too.
7. **Small redirects to update.** The Remarkety Yotpo guide moved to a "...-for-reviews" address.
   Braze and Optimizely help pages moved to new paths, and the old links forward to them. The
   addresses above are the current ones.
8. **Remarkety has thin mechanics docs.** I found one useful page about its journeys. Its help
   centre doesn't explain re-entry or what is checked again at send time.
9. **Optimizely's campaign basics page is marked "legacy"** in its address. It may describe the
   older campaign tool. The enrollment page next to it is current.
