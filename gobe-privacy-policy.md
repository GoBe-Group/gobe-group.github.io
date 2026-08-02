# GoBe — Privacy Policy

**Last updated:** 2 August 2026

> This is the hosted version of GoBe's Privacy Policy. It is generated from and kept in sync with the in-app version.

## 1. Introduction

This Privacy Policy explains what information Hamed Bakayoko, an individual sole trader (trading as "GoBe," "we," "us," or "our") of 124 City Road, London EC1V 2NX, United Kingdom, collects through the GoBe mobile app (the "App"), how we use and store it, who we share it with, and the choices and rights you have. We are the data controller for your personal data and are registered with the UK Information Commissioner's Office (ICO) under registration number C1991885. This is a privacy notice, not a contract. Creating an account confirms that you were shown this notice; where we rely on consent, we ask for that consent separately.

GoBe's core feature lets you record a "Trail" — the path you walk, run, or travel — and drop "Traces" — short notes, optional photos, and pinned locations — along the way, then view them on a map. Because that feature depends on your real-world location and movement, this policy gives specific detail about location, motion, and content data.

## 2. Account & Sign-In Information

GoBe offers two ways to create and authenticate your account.

- Sign in with Apple — Apple shares your name and email address with us, including the private, randomly generated "relay" email Apple provides if you choose to hide your real email address.
- Email and username sign-up — we collect the email address you give us (confirmed with a one-time code sent to it), and the username and password you choose. Passwords are handled by our authentication provider and are never stored in plain text.

We use this information to create your GoBe account, to sign you in, and to identify you across sessions.

Authentication and session management are handled by Supabase (specifically its GoTrue auth service). Supabase issues and stores the access and refresh tokens that keep you signed in, and associates them with your account record.

## 3. Profile Information

When you set up your profile, we collect the display name and username you choose, your date of birth (the App requires you to confirm you are at least 16 years old), and, optionally, an avatar photo you upload. This information is shown to you within the App and, depending on the feature, may be visible to other users — for example, your display name and avatar on a Trail or Trace.

Being found. Other signed-in users can search for people by display name or username, so your profile can be reached by someone who has not crossed paths with you in the App. Search results show only your display name, username, avatar and profile line — never your location. Anyone you have blocked, and anyone who has blocked you, is excluded from your search results and you from theirs.

## 4. Location Information

GoBe is built around your real-world location. We request "precise" (full-accuracy) location access and background location access. Background access lets the App keep logging your location while you are actively recording a Trail, so a Trail captures your complete route even when your phone is locked or the App is in the background.

We use location data to: draw the path of the Trail you're recording; place Traces at an approximate location near where you created them; show your trails and traces on the map; improve the accuracy of recorded routes; and warn you before you post a Trace inside one of your protected areas. You can stop a recording, or revoke location permission at any time in iOS Settings, though doing so will prevent Trails and Traces from being recorded.

Approximate Traces. To avoid revealing exactly where you are, GoBe never stores the exact coordinate of a Trace. Before a Trace is saved — both on your device and on our servers — its location is rounded to a coarse grid (roughly 30 metres), so a Trace shares a place, not your precise whereabouts. Your recorded Trail path is more detailed, but Trails are private to you by default and are not shown to other users.

Protected areas. You can mark one or more places as "protected areas" — your home, your workplace, the gym, or anywhere else you'd rather keep off the map. You choose each area yourself on a map in the App; GoBe does not detect or learn them for you. Each protected area is stored only on your device — it is never uploaded to our servers or shared with anyone. When you go to post a Trace inside an enabled protected area, GoBe warns you first so you can choose to move away. You can add, rename, switch off, or delete your protected areas at any time in the App's profile screen.

Because GoBe records where you go, your location data can sometimes reveal sensitive ("special category") information about you — for example, a place of worship, a health clinic, or a demonstration. We do not seek to infer special category information about you, and we ask you not to use locations to reveal such information about yourself or others. For users we understand to be under 18, we apply more protective defaults (see "Children & Users Under 18").

## 5. Motion & Fitness Information

GoBe reads step-count data from your device's motion co-processor (via Apple's Core Motion / pedometer APIs) to show step counts associated with your activity. We do not access your broader Health app data beyond step counts surfaced through Core Motion.

## 6. Your Content

GoBe stores the content you create:

- Traces — text notes, an optional photo, and an approximate (coarsely rounded) location near where you created them. We do not store the exact coordinate of a Trace.
- Trails — the sequence of GPS coordinates and timestamps that make up a recorded route, along with any title or metadata you add.

This content is stored on our servers (described below) so it can sync across your sessions and, where the App's sharing features allow it, be viewed by other users. Traces may be visible to other signed-in users; Trails are private to you by default.

Choosing photos. When you set a profile picture, Apple's system photo picker lets you browse your Photos albums without giving GoBe general access to your library. GoBe receives only the individual image you choose, and only that image is uploaded. If another photo feature asks for library permission, iOS lets you limit access to selected photos.

Reports and blocks. If you report a Trace, we keep a record of the report: your account, the reported content and its author, the reason you chose, and when you filed it. We use this to review the report and to meet our content moderation duties under the Online Safety Act 2023. Reports are visible only to us, never to other users. If you block someone, we store your block list (your account and the accounts you have blocked) so that their content stays hidden from you. Your block list is private to you, and the people you block are not told about it.

Friends, invites and your GoBe Score. When you add another user as a friend (a mutual "bond"), we store the connection between your two accounts so we can show it to you both and deliver friend requests. If you invite someone with your personal invite code, or join using a friend's code, we store the link between the inviting account and the joining account so we can attribute the referral. We also calculate a "GoBe Score" — a single number derived from your own activity (traces, trails, retraces, likes, comments and successful invites) and the reactions your traces receive. Your GoBe Score is shown on your profile and is visible to other signed-in users; it does not reveal your location or the content of any private Trail.

Achievements. We record the milestones your account passes — for example your first Trace, ten Trails, or a number of steps walked — along with the date each was reached. They are worked out from activity we already hold (your traces, trails, steps, friends, the likes and retraces your traces receive, and your GoBe Score) and are shown on your profile to other signed-in users. An achievement shows what you have done, never where: it does not name a place or reveal the content of any Trace or Trail.

## 7. How We Use Your Information

We use the information described above to: operate the App's core features (recording trails, placing traces, displaying your map); create and secure your account; authenticate you across devices and sessions; display your profile and content to you and, where applicable, to other users; moderate content and keep the service safe; maintain and improve the App's reliability and features; respond to support requests; and meet legal obligations. We also use it to send you notifications about activity that involves you — such as a like, comment, or retrace on your trace, or a friend request — and occasional GoBe progress or exploration prompts such as territory recaps, ranking movement, milestone prompts and return reminders. These are controlled together by the single Notifications switch in the App's profile screen and by iOS Settings. GoBe's progress and exploration prompts use your activity, GoBe Score and area standing. We do not sell your personal information, and we do not use your location or content data for third-party advertising.

## 8. Our Legal Bases for Using Your Data

Where the UK GDPR, EU GDPR, or a similar law requires a legal basis, we rely on:

- Contract — to create and run your account and provide the core features you request.
- Consent — for device access to precise and background location, motion/step data, and optional promotional notifications where consent is required. You can withdraw consent in the App or iOS Settings without affecting earlier lawful processing, although the related feature may stop working.
- Legitimate interests — to secure and improve GoBe, prevent abuse, calculate service statistics, and moderate content, after balancing those interests against your rights.
- Legal obligation — to comply with privacy, safety, consumer, and other applicable laws and lawful requests.
- Vital interests or public interest — only in the exceptional circumstances in which applicable law permits and the basis genuinely applies.

Where another privacy law uses different grounds, we process information only for purposes permitted by that law.

## 9. Where Your Information Is Stored

GoBe's backend runs on Supabase. Your account record, profile, trails, and trace data are stored in a Supabase Postgres database. Photos you upload — avatars and trace photos — are stored in Supabase Storage, in buckets named "avatars" and "post-images." Our Supabase project is hosted in the EU (eu-central-1 / Frankfurt region).

These photo storage buckets are private: photos are not publicly accessible and can only be retrieved by signed-in users through an access-controlled endpoint, governed by row-level security policies. A photo cannot be viewed by someone simply because they have guessed or obtained a storage link.

## 10. Third Parties & Sub-Processors

We share information with a limited number of service providers who help us run GoBe:

- Apple — provides "Sign in with Apple" authentication and, if you choose, relays your email through its private-relay service.
- Supabase — provides our database, file storage, and authentication (GoTrue) infrastructure, and stores the data described in this policy on our behalf, hosted in the EU.
- PostHog — provides anonymous usage statistics and crash reporting, hosted in the EU. We record a small set of app events (for example that a trail was started, or that the app crashed and where in the code it happened) so we can fix problems and see which features are used. These events are anonymous: we configure PostHog so that no user profile is built about you, and no event ever includes your location, your content, your name, or your email.
- Cloudflare — provides DNS, content delivery, and security filtering for our public website, which hosts this policy, our terms, and our support pages. When you visit that website, Cloudflare processes your IP address and basic request information (such as the page requested and your browser type) in order to serve the page and to block abusive traffic. Cloudflare has no access to your GoBe account, trails, or traces.

We do not share your personal information with advertisers or data brokers. We may disclose information if required by law, to protect the rights and safety of GoBe or its users, or in connection with a sale of the business, in which case we'll make reasonable efforts to notify you.

## 11. Data Retention

We keep your account, profile, trail, and trace data for as long as your account is active, so the App can show you your history and keep your content in sync. If you delete your account (see below), we delete or anonymise this data within 30 days, except where we are required to keep limited records longer for legal, security, or fraud-prevention purposes — in which case we keep only what is necessary, for no longer than required.

## 12. Your Rights & Choices

Depending on where you live, you may have rights to know or access the information we hold about you; correct, delete, or receive a portable copy of it; object to or restrict processing; withdraw consent; opt out of certain disclosures, targeted advertising, or profiling; appeal a refused request; and complain to a privacy authority. We do not sell personal information or use it for third-party targeted advertising.

You can review and edit profile information in the App, delete your account using "Delete Account," and revoke device permissions in iOS Settings. You may also email contact@gobeapp.co.uk. We may verify your identity before completing a request and will respond within the period required by the law that applies to you. We will not discriminate against you for exercising a privacy right.

## 13. Children & Users Under 18

GoBe is not for anyone under 16. We use the date of birth entered at sign-up to enforce that rule and do not permit an account to be created when the stated age is under 16. If we discover that we collected information from an under-16 user, we will close the account and delete the information unless law requires limited retention.

For users aged 16 or 17, we apply high-privacy defaults, minimise collection, and limit location sharing by default. In the UK we take account of the ICO's Age Appropriate Design Code. In the United States, GoBe is a general-audience service and is not directed to children under 13; if we gain actual knowledge that we collected a child's information, we will delete it and take the action required by COPPA. Parents or guardians may contact contact@gobeapp.co.uk.

## 14. Security

We use reasonable technical and organisational measures — including encrypted connections (HTTPS/TLS) and database and storage access controls — to protect your information. Supabase maintains its own security programme for the systems it operates on our behalf. No method is completely secure. If a personal data breach occurs, we will notify affected people and the appropriate authorities where and within the time required by applicable law.

## 15. International Data Transfers

Our primary Supabase servers are hosted in the EU (eu-central-1 / Frankfurt). Information may also be processed in other countries by the providers listed above. Depending on the originating country, we rely on adequacy decisions, contractual safeguards such as approved standard contractual clauses or the UK International Data Transfer Agreement/Addendum, or another lawful transfer mechanism. You may contact us for information about the safeguard relevant to your data.

## 16. Changes to This Policy

We may update this Privacy Policy when our practices or legal obligations change. We will update the "Last Updated" date and notify you in the App or by email when a change is material. If a change requires consent, we will ask for it separately. Continued use is not treated as consent to new processing that legally requires consent.

## 17. Regional Privacy Information

United Kingdom. UK residents may exercise UK GDPR rights and complain to the Information Commissioner's Office at ico.org.uk.

European Economic Area. If the EU GDPR applies, you may exercise the rights described above and complain to the supervisory authority where you live, work, or believe an infringement occurred. Before specifically offering GoBe to people in the EEA, we will publish the details of any EU representative required by Article 27. EEA launch remains subject to completing that appointment assessment.

United States. Residents of states with applicable comprehensive privacy laws may request access, correction, deletion, or portability and may opt out of sale, targeted advertising, or qualifying profiling as provided by their state law. GoBe does not sell personal information, share it for cross-context behavioural advertising, or use it for third-party targeted advertising. We process precise route location only to provide requested GoBe features, security, and legal compliance. Where required, you may appeal a decision by replying to our response. California residents may also request the categories of information, sources, purposes, and recipients described in this Policy. These rights apply when the relevant law covers GoBe.

Canada. You may request access to and correction of personal information and challenge our compliance through the contact below. We use consent or another lawful basis recognised by applicable federal or provincial law.

Brazil. Where the LGPD applies, you may request confirmation of processing, access, correction, anonymisation, blocking or deletion where applicable, portability, information about sharing, withdrawal of consent, and review of qualifying automated decisions. Contact is available at contact@gobeapp.co.uk.

Australia. Where the Privacy Act 1988 and Australian Privacy Principles apply, you may request access or correction and complain to us. If unresolved, you may contact the Office of the Australian Information Commissioner.

Japan. Where the APPI applies, you may request disclosure, correction, suspension of use, or deletion as provided by law and ask about cross-border handling through the contact below.

## 18. Contact Us

If you have questions about this Privacy Policy, want to exercise your privacy rights, or want to request deletion of your data, contact Hamed Bakayoko, trading as GoBe, of 124 City Road, London EC1V 2NX, United Kingdom, at contact@gobeapp.co.uk.
