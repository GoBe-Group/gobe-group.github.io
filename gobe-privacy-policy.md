# GoBe — Privacy Policy

**Last updated:** 22 September 2026

> This is the hosted version of GoBe's Privacy Policy. It is generated from and kept in sync with the in-app version.

## 1. Introduction

This Privacy Policy explains what information Hamed Bakayoko, an individual sole trader (trading as "GoBe," "we," "us," or "our") of 124 City Road, London EC1V 2NX, United Kingdom, collects through the GoBe mobile app (the "App"), how we use and store it, who we share it with, and the choices and rights you have. We are the data controller for your personal data and are registered with the UK Information Commissioner's Office (ICO) under registration number C1991885. This is a privacy notice, not a contract. Creating an account confirms that you were shown this notice; where we rely on consent, we ask for that consent separately.

GoBe's core feature lets you record a "Trail" — the path you walk, run, or travel — and drop "Traces" — short notes, optional photos or videos, any text you add on top of them, and pinned locations — along the way, then view them on a map. Because that feature depends on your real-world location and movement, this policy gives specific detail about location, motion, and content data.

## 2. Account & Sign-In Information

GoBe offers two ways to create and authenticate your account.

- Sign in with Apple — Apple shares your name and email address with us, including the private, randomly generated "relay" email Apple provides if you choose to hide your real email address.
- Email and username sign-up — we collect the email address you give us (confirmed with a one-time code sent to it), and the username and password you choose. Passwords are handled by our authentication provider and are never stored in plain text.

We use this information to create your GoBe account, to sign you in, and to identify you across sessions.

Authentication and session management are handled by Supabase (specifically its GoTrue auth service). Supabase issues and stores the access and refresh tokens that keep you signed in, and associates them with your account record.

## 3. Profile Information

When you set up your profile, we collect the display name and username you choose, your date of birth (the App requires you to confirm you are at least 16 years old), your phone number, and, optionally, an avatar photo you upload. This information is shown to you within the App and, depending on the feature, may be visible to other users — for example, your display name and avatar on a Trail or Trace.

Your phone number. Setting up an account requires a phone number; there is no way to finish signing up without giving one. We store it in international format and use it to secure and recover your account, to contact you about your account where email is not enough, and to help prevent one person from creating many accounts. It is never shown on your profile, never returned to another user by search or by any other feature in the App, and never shared with advertisers or data brokers. Technically it is held in a separate table from the rest of your profile, readable only by your own account, precisely so that it cannot be read by other users the way your display name and avatar can. We confirm it by texting you a one-time code when you sign up (or later, from People you know), so that a number on an account belongs to the person using it; a number can be confirmed on only one GoBe account. We do not use it to send you marketing. Once your number is confirmed, people who already have it in their contacts can find you on GoBe, as described in section 6, and you can switch that off at any time. Your number is deleted with your account.

Being found. Other signed-in users can search for people by display name or username, so your profile can be reached by someone who has not crossed paths with you in the App. The App may also suggest your profile to other signed-in users as somebody they could connect with, either because you left a Trace near them or simply because you have an account; a suggestion shows the same details a search does and never says where you are or have been. Search results and suggestions show only your display name, username, avatar and profile line — never your location. Anyone you have blocked, and anyone who has blocked you, is excluded from your search results and you from theirs.

## 4. Location Information

GoBe is built around your real-world location. We request "precise" (full-accuracy) location access and background location access. Background access lets the App keep logging your location while you are actively recording a Trail, so a Trail captures your complete route even when your phone is locked or the App is in the background.

We use location data to: draw the path of the Trail you're recording; place Traces at an approximate location near where you created them; show your trails and traces on the map; improve the accuracy of recorded routes; and warn you before you post a Trace inside one of your protected areas. You can stop a recording, or revoke location permission at any time in iOS Settings, though doing so will prevent Trails and Traces from being recorded.

Approximate Traces. To avoid revealing exactly where you are, GoBe never stores the exact coordinate of a Trace. Before a Trace is saved — both on your device and on our servers — its location is rounded to a coarse grid (roughly 30 metres), so a Trace shares a place, not your precise whereabouts. Your recorded Trail path is more detailed, but Trails are private to you by default and are not shown to other users.

Protected areas. You can mark one or more places as "protected areas" — your home, your workplace, the gym, or anywhere else you'd rather keep off the map. You choose each area yourself on a map in the App; GoBe does not detect or learn them for you. Each protected area is stored only on your device — it is never uploaded to our servers or shared with anyone. When you go to post a Trace inside an enabled protected area, GoBe warns you first so you can choose to move away. You can add, rename, switch off, or delete your protected areas at any time in the App's profile screen.

People you cross (on your device only). When you come close enough to another person's Trace to open it, GoBe keeps a note on your device that you crossed that person, so you can find them again afterwards. This is worked out entirely on your phone from Traces that were already published to the map and already within your reach; nothing extra is sent to our servers, and no new information about the other person is revealed to you. The note holds who you crossed, when, how many of their marks you have reached and, when the App already knows it, the name of the neighbourhood you were in. It never records where the other person was, and it is never shown to them. It is kept only on this device, is deleted when you sign out, and a person you block is removed from it. Your recorded Trails are never used for this, and are never compared with anybody else's.

Because GoBe records where you go, your location data can sometimes reveal sensitive ("special category") information about you — for example, a place of worship, a health clinic, or a demonstration. We do not seek to infer special category information about you, and we ask you not to use locations to reveal such information about yourself or others. For users we understand to be under 18, we apply more protective defaults (see "Children & Users Under 18").

## 5. Motion & Fitness Information

GoBe reads step-count data from your device's motion co-processor (via Apple's Core Motion / pedometer APIs) to show step counts associated with your activity. We do not access your broader Health app data beyond step counts surfaced through Core Motion.

## 6. Contacts & Finding People You Know

GoBe can help you find people you already know who are also on GoBe.

- Being findable. Once your phone number has been confirmed by a code (see section 3), people who already have that number in their contacts can find you on GoBe. This is on by default, and you can switch it off at any time in the App under Profile, People you know. For this, our servers keep an irreversible scrambled version of your number (a salted cryptographic hash), and that is what the matching uses: it never shows your number to anyone. Switching it off deletes that value.
- Finding others. If you ask GoBe to check your contacts, the App asks for access to your address book and reads it on your device only. Your contacts are never uploaded. The App downloads a deliberately incomplete list of scrambled values, compares it against your contacts on the device, and sends back only the small number of entries that already appear to match, in scrambled form, so that we can tell you who they are. Contacts that do not match are never disclosed to us in any form.

We use this only to show you people you may know. We do not use it to build a social graph of people who are not GoBe users, we do not keep your address book, and we do not share any of it with third parties. Because being findable is on by default, we rely on our legitimate interest in helping people who already know each other find one another on GoBe; you can object at any time by switching it off.

## 7. Your Content

GoBe stores the content you create:

- Traces — text notes, an optional photo or short video, any caption or text you place on that photo or video (before or after posting), and an approximate (coarsely rounded) location near where you created them. We do not store the exact coordinate of a Trace.
- Trails — the sequence of GPS coordinates and timestamps that make up a recorded route, along with any title or metadata you add.

This content is stored on our servers (described below) so it can sync across your sessions and, where the App's sharing features allow it, be viewed by other users. Traces may be visible to other signed-in users; Trails are private to you by default.

Choosing photos. When you set a profile picture, Apple's system photo picker lets you browse your Photos albums without giving GoBe general access to your library. GoBe receives only the individual image you choose, and only that image is uploaded. If another photo feature asks for library permission, iOS lets you limit access to selected photos.

Reports and blocks. If you report a Trace, or a community or event, we keep a record of the report: your account, a copy of the reported content and its author, the reason you chose, and when you filed it. We keep the copy so the report stays reviewable even if the content is deleted afterwards. We use this to review the report and to meet our content moderation duties under the Online Safety Act 2023. Reports are visible only to us, never to other users. If you block someone, we store your block list (your account and the accounts you have blocked) so that their content stays hidden from you. Your block list is private to you, and the people you block are not told about it.

Friends, invites and your GoBe Score. When you add another user as a friend (a mutual "bond"), we store the connection between your two accounts so we can show it to you both and deliver friend requests. If you invite someone with your personal invite code, or join using a friend's code, we store the link between the inviting account and the joining account so we can attribute the referral. We also calculate a "GoBe Score" — a single number derived from your own activity (traces, trails, retraces, likes, comments, the people you are connected with, and successful invites) and the reactions your traces receive. Your GoBe Score is shown on your profile and is visible to other signed-in users; it does not reveal your location or the content of any private Trail.

Messages. You can send a message to someone you have both added as a friend, and to the chat of a community or event you have joined. We store what you write, who sent it, which conversation it is in, when it was sent, and how far each person has read. A message you send to a friend can be read by the two of you; a message in a community's or event's chat can be read by everyone who has joined it, including people who join later. Nobody else can read your messages, and we do not look at them unless someone in the conversation reports one, in which case we keep a copy with the report, as we do for any other report. If you and a friend stop being friends, what you both said stays readable to you both but neither of you can send more; if either of you blocks the other, the conversation is hidden from you both. If you leave a community or event, its chat closes to you. Messages are deleted with your account.

Communities and events. You can start a "community" (a standing group) or an "event" (a dated one) and pin it to a place on the map. We store its name, the short description and character you choose for it, the coordinate and radius you place it at, when an event starts and finishes, whether anyone may join or you approve each person, and who has joined or asked to join. A community or event you start is visible on the map to any signed-in user, so please do not give one a name or description you would not want strangers to read, and do not pin one to your home. Who has joined is shown to the people who have joined it, and to whoever started it; a request to join is visible only to you and to whoever started it.

What joining changes. When you leave a Trace you may choose to leave it to one community or event you belong to. Doing so lets everyone who has joined that community or event open that Trace from anywhere, instead of having to be near it. It changes nothing else: your other Traces keep their normal visibility, your Trails stay private, and nobody gains access to your location or your account. The choice is made on each Trace as you leave it and is never applied to a Trace retrospectively, so joining a group can never open Traces you left before you joined. If you leave a community or event, its Traces close to you again. An event only accepts a Trace left inside its area while it is on. Whoever started a community or event can call it off; the Traces left to it remain yours and stay on the map, but stop being shared through it.

Traces left without a name. When you leave a Trace you may choose to leave it anonymously. Other users are then not shown who left it: the App draws it with a mask instead of your picture and your username, no other user can see it listed on your profile, and it counts toward nobody's GoBe Score or area ranking. Two things it does not mean. It is anonymous to other users, not to us: our records still hold that the Trace is yours, because we have to be able to act on a report about it, to delete it with your account, and to give it to you if you ask for a copy of your data. And it does not hide where the Trace is, which is the point of leaving one; it is stored on the same coarse grid as every other Trace. The choice is made on each Trace as you leave it and is not applied to Traces retrospectively.

Feedback. Now and then the App asks how GoBe is going. If you answer that it could be better, we store what you write, your account, and which version of the App you were using, so that we can read it, reply if you have asked us to, and fix what you have told us about. It is visible only to us, never to other users, and what you write is never sent to our analytics provider. It is deleted with your account.

Achievements. We record the milestones your account passes — for example your first Trace, ten Trails, or a number of steps walked — along with the date each was reached. They are worked out from activity we already hold (your traces, trails, steps, friends, the likes and retraces your traces receive, and your GoBe Score) and are shown on your profile to other signed-in users. An achievement shows what you have done, never where: it does not name a place or reveal the content of any Trace or Trail.

## 8. How We Use Your Information

We use the information described above to: operate the App's core features (recording trails, placing traces, displaying your map); create and secure your account; authenticate you across devices and sessions; display your profile and content to you and, where applicable, to other users; moderate content and keep the service safe; maintain and improve the App's reliability and features; respond to support requests; and meet legal obligations. We also use it to send you notifications about activity that involves you — such as a like, comment, or retrace on your trace, or a friend request; about what the people you have added have been doing, such as leaving a trace, liking or commenting on one, or starting a community or event, which we tell you with their username on it because adding someone is mutual and both of you agreed to it; about new messages sent to you or to a community or event you have joined, which you can mute for each conversation; about activity in an area you have left a trace in yourself, which never names the person and says only that someone left a trace and which area it was in; about a trace left on the grounds of a university you have joined on GoBe, which likewise never names the person and says only that someone left a trace and which campus it was on, at most once every three hours for each campus; a weekly summary, on Sunday evening, of how many times your traces were walked to, liked or commented on that week, which names nobody and is not sent when nothing happened; and occasional GoBe progress or exploration prompts such as territory recaps, ranking movement, milestone prompts and return reminders. These are controlled together by the single Notifications switch in the App's profile screen and by iOS Settings. GoBe's progress and exploration prompts use your activity, GoBe Score and area standing.

Traces near you. If notifications are on, your phone can tell you when someone's trace comes within reach of you while you are out. This one is put together on your device and nowhere else: our servers are never told where you are in order to send it, because the App already works out what is within reach in order to show it to you at all. It says that someone left a trace near you. It does not say who, it does not say where, and it is limited to once an hour.

Put together on your phone. Two more notifications are worked out on your device and scheduled there, without our servers being told anything in order to send them: a note the next morning saying how many people you crossed paths with since the last one (a number only, never who or where), if you have not left a trace yet, one reminder the next evening, which is taken back the moment you leave one; and, if you have been out several days in a row, an evening reminder on a day you have not left a trace or gone for a walk yet. The count of days is worked out from the traces and walks already on your phone.

Email. We use the email address on your account for two different purposes, and only one of them is optional.

- Service email, which we send because you have an account: confirming your address, resetting your password, security notices, a reply when you contact us, and notice of a material change to this policy or our Terms. These are not marketing and cannot be switched off while your account exists.
- Marketing email, which we send only if you ask us to: occasional word about new features and what's happening near you, no more than once a month. The App no longer offers a way to turn this on, so no new account can be opted in to it. Every marketing email carries a one-click unsubscribe link that works without signing in, which is how anybody who turned it on before that switch was removed can turn it off. We record when you turned it on, which version of this policy was in force at the time, and every later change, so that we can show the consent we are relying on.

We do not sell your personal information, we do not share your email address with advertisers or data brokers, and we do not use your location or content data for third-party advertising.

## 9. Our Legal Bases for Using Your Data

Where the UK GDPR, EU GDPR, or a similar law requires a legal basis, we rely on:

- Contract — to create and run your account and provide the core features you request.
- Consent — for device access to precise and background location, motion/step data, optional promotional notifications, and marketing email, where consent is required. Marketing email is sent only with your consent under regulation 22 of the Privacy and Electronic Communications Regulations 2003; we do not rely on the "soft opt-in" exception, because GoBe does not sell you anything. You can withdraw consent in the App, in iOS Settings, or through the unsubscribe link in any marketing email, without affecting earlier lawful processing, although the related feature may stop working.
- Legitimate interests — to secure and improve GoBe, prevent abuse, calculate service statistics, and moderate content, after balancing those interests against your rights.
- Legal obligation — to comply with privacy, safety, consumer, and other applicable laws and lawful requests.
- Vital interests or public interest — only in the exceptional circumstances in which applicable law permits and the basis genuinely applies.

Where another privacy law uses different grounds, we process information only for purposes permitted by that law.

## 10. Where Your Information Is Stored

GoBe's backend runs on Supabase. Your account record, profile, trails, and trace data are stored in a Supabase Postgres database. Photos you upload — avatars and trace photos — are stored in Supabase Storage, in buckets named "avatars" and "post-images." Our Supabase project is hosted in the EU (eu-central-1 / Frankfurt region).

These photo storage buckets are private: photos are not publicly accessible and can only be retrieved by signed-in users through an access-controlled endpoint, governed by row-level security policies. A photo cannot be viewed by someone simply because they have guessed or obtained a storage link.

## 11. Third Parties & Sub-Processors

We share information with a limited number of service providers who help us run GoBe:

- Apple — provides "Sign in with Apple" authentication and, if you choose, relays your email through its private-relay service.
- Supabase — provides our database, file storage, and authentication (GoTrue) infrastructure, and stores the data described in this policy on our behalf, hosted in the EU.
- Twilio: sends the one-time codes that confirm your phone number, by text message. Twilio receives your phone number and the code, and nothing else about your account.
- PostHog — provides anonymous usage statistics and crash reporting, hosted in the EU. We record a small set of app events (for example that a trail was started, or that the app crashed and where in the code it happened) so we can fix problems and see which features are used. These events are anonymous: we configure PostHog so that no user profile is built about you, and no event ever includes your location, your content, your name, or your email. We also record some sessions in the App as a replay, a picture of the screens you move through and where you tap, so we can see where the App is confusing or broken. Maps, photos, and anything you type are blacked out on your phone before a replay is sent, and messages, settings, sign-in, and the trace composer are not recorded at all. Replays are kept for 30 days and are deleted with your account.
- Cloudflare — provides DNS, content delivery, and security filtering for our public website, which hosts this policy, our terms, and our support pages. When you visit that website, Cloudflare processes your IP address and basic request information (such as the page requested and your browser type) in order to serve the page and to block abusive traffic. Cloudflare has no access to your GoBe account, trails, or traces.

We do not share your personal information with advertisers or data brokers. We may disclose information if required by law, to protect the rights and safety of GoBe or its users, or in connection with a sale of the business, in which case we'll make reasonable efforts to notify you.

## 12. Data Retention

We keep your account, profile, trail, and trace data for as long as your account is active, so the App can show you your history and keep your content in sync. If you delete your account (see below), we delete or anonymise this data within 30 days, except where we are required to keep limited records longer for legal, security, or fraud-prevention purposes — in which case we keep only what is necessary, for no longer than required.

Marketing consent records. If you turn marketing email on or off, we keep a dated record of that change for as long as your account exists, so that we can evidence the consent we relied on when we sent you something. The record holds the change itself, its date and how it was made — it does not hold the content of any email. It is deleted with your account.

## 13. Your Rights & Choices

Depending on where you live, you may have rights to know or access the information we hold about you; correct, delete, or receive a portable copy of it; object to or restrict processing; withdraw consent; opt out of certain disclosures, targeted advertising, or profiling; appeal a refused request; and complain to a privacy authority. We do not sell personal information or use it for third-party targeted advertising.

You can review and edit profile information in the App, delete your account using "Delete Account," revoke device permissions in iOS Settings, and stop marketing email with the unsubscribe link in any such email, which works without signing in. You may also email contact@gobeapp.co.uk. We may verify your identity before completing a request and will respond within the period required by the law that applies to you. We will not discriminate against you for exercising a privacy right.

## 14. Children & Users Under 18

GoBe is not for anyone under 16. We use the date of birth entered at sign-up to enforce that rule and do not permit an account to be created when the stated age is under 16. If we discover that we collected information from an under-16 user, we will close the account and delete the information unless law requires limited retention.

For users aged 16 or 17, we apply high-privacy defaults, minimise collection, and limit location sharing by default. In the UK we take account of the ICO's Age Appropriate Design Code. In the United States, GoBe is a general-audience service and is not directed to children under 13; if we gain actual knowledge that we collected a child's information, we will delete it and take the action required by COPPA. Parents or guardians may contact contact@gobeapp.co.uk.

## 15. Security

We use reasonable technical and organisational measures — including encrypted connections (HTTPS/TLS) and database and storage access controls — to protect your information. Supabase maintains its own security programme for the systems it operates on our behalf. No method is completely secure. If a personal data breach occurs, we will notify affected people and the appropriate authorities where and within the time required by applicable law.

## 16. International Data Transfers

Our primary Supabase servers are hosted in the EU (eu-central-1 / Frankfurt). Information may also be processed in other countries by the providers listed above. Depending on the originating country, we rely on adequacy decisions, contractual safeguards such as approved standard contractual clauses or the UK International Data Transfer Agreement/Addendum, or another lawful transfer mechanism. You may contact us for information about the safeguard relevant to your data.

## 17. Changes to This Policy

We may update this Privacy Policy when our practices or legal obligations change. We will update the "Last Updated" date and notify you in the App or by email when a change is material. If a change requires consent, we will ask for it separately. Continued use is not treated as consent to new processing that legally requires consent.

## 18. Regional Privacy Information

United Kingdom. UK residents may exercise UK GDPR rights and complain to the Information Commissioner's Office at ico.org.uk.

European Economic Area. If the EU GDPR applies, you may exercise the rights described above and complain to the supervisory authority where you live, work, or believe an infringement occurred. Before specifically offering GoBe to people in the EEA, we will publish the details of any EU representative required by Article 27. EEA launch remains subject to completing that appointment assessment.

United States. Residents of states with applicable comprehensive privacy laws may request access, correction, deletion, or portability and may opt out of sale, targeted advertising, or qualifying profiling as provided by their state law. GoBe does not sell personal information, share it for cross-context behavioural advertising, or use it for third-party targeted advertising. We process precise route location only to provide requested GoBe features, security, and legal compliance. Where required, you may appeal a decision by replying to our response. California residents may also request the categories of information, sources, purposes, and recipients described in this Policy. These rights apply when the relevant law covers GoBe.

Canada. You may request access to and correction of personal information and challenge our compliance through the contact below. We use consent or another lawful basis recognised by applicable federal or provincial law.

Brazil. Where the LGPD applies, you may request confirmation of processing, access, correction, anonymisation, blocking or deletion where applicable, portability, information about sharing, withdrawal of consent, and review of qualifying automated decisions. Contact is available at contact@gobeapp.co.uk.

Australia. Where the Privacy Act 1988 and Australian Privacy Principles apply, you may request access or correction and complain to us. If unresolved, you may contact the Office of the Australian Information Commissioner.

Japan. Where the APPI applies, you may request disclosure, correction, suspension of use, or deletion as provided by law and ask about cross-border handling through the contact below.

## 19. Contact Us

If you have questions about this Privacy Policy, want to exercise your privacy rights, or want to request deletion of your data, contact Hamed Bakayoko, trading as GoBe, of 124 City Road, London EC1V 2NX, United Kingdom, at contact@gobeapp.co.uk.
