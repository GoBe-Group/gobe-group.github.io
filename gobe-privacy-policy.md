# GoBe — Privacy Policy

**Last updated:** 4 July 2026

> This is the hosted version of GoBe's Privacy Policy. It is kept word-for-word in sync with the in-app version (`Legal/PrivacyPolicyContent.swift`). Change both together. Once registered with the ICO (ico.org.uk — the data protection fee), add back to section 1: "…, and we are registered with the UK Information Commissioner's Office (ICO) under registration number <number>."

## 1. Introduction

This Privacy Policy explains what information Hamed Bakayoko, an individual sole trader (trading as "GoBe," "we," "us," or "our") of 35 Cheshire Close, CR4 1XF, United Kingdom, collects through the GoBe mobile app (the "App"), how we use and store it, who we share it with, and the choices and rights you have. We are the data controller for your personal data. This policy is provided under, and should be read together with, the UK GDPR and the Data Protection Act 2018. By using the App you agree to this Privacy Policy. If you do not agree, please do not use the App.

GoBe's core feature lets you record a "Trail" — the path you walk, run, or travel — and drop "Traces" — short notes, optional photos, and pinned locations — along the way, then view them on a map. Because that feature depends on your real-world location and movement, this policy goes into specific detail about the location, motion, and content data the App collects.

## 2. Account & Sign-In Information

GoBe offers two ways to create and authenticate your account.

- **Sign in with Apple** — Apple shares your name and email address with us, including the private, randomly generated "relay" email Apple provides if you choose to hide your real email address.
- **Email and username sign-up** — we collect the email address you give us (confirmed with a one-time code sent to it), and the username and password you choose. Passwords are handled by our authentication provider and are never stored in plain text.

We use this information to create your GoBe account, to sign you in, and to identify you across sessions.

Authentication and session management are handled by Supabase (specifically its GoTrue auth service). Supabase issues and stores the access and refresh tokens that keep you signed in, and associates them with your account record.

## 3. Profile Information

When you set up your profile, we collect the display name and username you choose, your date of birth (the App requires you to confirm you are at least 16 years old), and, optionally, an avatar photo you upload. This information is shown to you within the App and, depending on the feature, may be visible to other users — for example, your display name and avatar on a Trail or Trace.

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

Choosing photos. When you set a profile picture or attach a photo to a Trace, the App accesses your device's photo library so you can pick an image. iOS lets you share your whole library or only the specific photos you select; either way, GoBe only ever receives the individual image you choose, and only that image is uploaded.

## 7. How We Use Your Information

We use the information described above to: operate the App's core features (recording trails, placing traces, displaying your map); create and secure your account; authenticate you across devices and sessions; display your profile and content to you and, where applicable, to other users; moderate content and keep the service safe; maintain and improve the App's reliability and features; respond to support requests; and meet legal obligations. We do not sell your personal information, and we do not use your location or content data for third-party advertising.

## 8. Our Legal Bases for Using Your Data

Under the UK GDPR, we rely on the following legal bases:

- **Contract** — to create and run your account and provide the core features you ask for (recording trails, placing traces, showing your map).
- **Consent** — for access to your precise and background location and your motion/step data. You can withdraw consent at any time in iOS Settings; this will not affect processing already carried out, but may disable the related feature.
- **Legitimate interests** — to keep GoBe secure, prevent abuse, moderate content, and improve the App, balanced against your rights and freedoms.
- **Legal obligation** — to meet our duties under data protection law and the Online Safety Act 2023, and to respond to lawful requests.

## 9. Where Your Information Is Stored

GoBe's backend runs on Supabase. Your account record, profile, trails, and trace data are stored in a Supabase Postgres database. Photos you upload — avatars and trace photos — are stored in Supabase Storage, in buckets named "avatars" and "post-images." Our Supabase project is hosted in the EU (eu-central-1 / Frankfurt region).

These photo storage buckets are private: photos are not publicly accessible and can only be retrieved by signed-in users through an access-controlled endpoint, governed by row-level security policies. A photo cannot be viewed by someone simply because they have guessed or obtained a storage link.

## 10. Third Parties & Sub-Processors

We share information with a limited number of service providers who help us run GoBe:

- **Apple** — provides "Sign in with Apple" authentication and, if you choose, relays your email through its private-relay service.
- **Supabase** — provides our database, file storage, and authentication (GoTrue) infrastructure, and stores the data described in this policy on our behalf, hosted in the EU.

We do not share your personal information with advertisers or data brokers. We may disclose information if required by law, to protect the rights and safety of GoBe or its users, or in connection with a sale of the business, in which case we'll make reasonable efforts to notify you.

## 11. Data Retention

We keep your account, profile, trail, and trace data for as long as your account is active, so the App can show you your history and keep your content in sync. If you delete your account (see below), we delete or anonymise this data within 30 days, except where we are required to keep limited records longer for legal, security, or fraud-prevention purposes — in which case we keep only what is necessary, for no longer than required.

## 12. Your Rights & Choices

Under the UK GDPR you have rights to access, correct, export, or delete your personal information, and to object to or restrict certain processing, and to withdraw consent. You can:

- Review and edit your profile information directly in the App.
- Delete your account and associated data at any time using "Delete Account" in the App's Account screen — this permanently removes your account, trails, and traces from our systems.
- Revoke location, motion, or photo-library permissions at any time in iOS Settings (note this will limit or disable core features).
- Contact us at hamedbakayoko048@gmail.com to make a data access, correction, or deletion request, or with any privacy question.

We will respond to verified requests within the timeframe required by law (usually one month). You also have the right to complain to the ICO at [ico.org.uk](https://ico.org.uk) if you are unhappy with how we handle your data.

## 13. Children & Users Under 18

GoBe is not for anyone under 16, and we ask for your date of birth at sign-up to enforce this. We do not knowingly collect personal information from anyone under 16, and we will delete such data if we discover it.

Because some of our users are 16 or 17 — who are still "children" under UK data protection law — we follow the ICO's Age Appropriate Design Code (the "Children's Code"). For users we understand to be under 18, we aim to apply high-privacy defaults, collect the minimum data needed, and keep location sharing limited by default. We have assessed, and keep under review, the risks our processing poses to younger users. If you are a parent or guardian with concerns, contact us at hamedbakayoko048@gmail.com.

## 14. Security

We use reasonable technical and organisational measures — including encrypted connections (HTTPS/TLS) between the App and our backend, and access controls on our database and storage — to protect your information. Supabase, our infrastructure provider, maintains its own security program for the systems it operates on our behalf. No method of transmission or storage is completely secure, however, and we cannot guarantee absolute security. If a personal data breach is likely to result in a risk to your rights, we will notify the ICO, and you where required, in line with our legal obligations.

## 15. International Data Transfers

Our servers are hosted in the EU (eu-central-1 / Frankfurt). Transfers of personal data from the UK to the EEA are permitted under the UK's adequacy arrangements. If we transfer personal data anywhere that is not covered by a UK adequacy decision, we put appropriate safeguards (such as the ICO's International Data Transfer Agreement) in place.

## 16. Changes to This Policy

We may update this Privacy Policy from time to time. If we make material changes, we will update the "Last Updated" date above and, where appropriate, notify you in the App. Your continued use of GoBe after a change takes effect means you accept the updated policy.

## 17. Contact Us

If you have questions about this Privacy Policy, want to exercise your privacy rights, or want to request deletion of your data, contact Hamed Bakayoko, trading as GoBe, of 35 Cheshire Close, CR4 1XF, United Kingdom, at hamedbakayoko048@gmail.com.
