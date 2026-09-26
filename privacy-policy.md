# Privacy Policy

**Last updated:** August 28, 2026

This Privacy Policy describes how the IMSEL VPN mobile application ("App") handles information when you use it. The App is provided free of charge by the IMSEL VPN developer ("We", "Us", "Developer"). Contact: [imsel.vpn@gmail.com](mailto:imsel.vpn@gmail.com).

## 1. Summary

- The App has **no accounts or registration** and does not require your name, email, or phone number.
- Your **VPN traffic is not logged and cannot be read** by the App: it is encrypted end-to-end between your device and your VPN server.
- We collect a **limited set of technical data**: a device identifier sent with subscription update requests, crash reports and anonymized usage events (AppMetrica), and advertising identifiers (Yandex Mobile Ads).
- You can **disable analytics** at any time with the "Send analytics" switch in the App's side menu.

## 2. Data We Collect

### 2.1 Device identifier (HWID)

- **What:** a device identifier — the Android ID (or a random UUID generated on the device when Android ID is unavailable; on iOS, the vendor identifier). Along with the identifier, subscription update requests include technical device headers: app version and User-Agent, device language, platform and OS version, and device model (Happ-compatible headers `x-device-locale`, `x-device-os`, `x-ver-os`, `x-device-model`).
- **Why:** the App sends this identifier in the `X-HWID` header with every subscription update request **to the subscription server you configured**. It is used to bind your device to your subscription service and to keep the advertising frequency counter fair (so that ad capping works per device). Device headers allow the provider to serve compatible subscription formats.
- **Where it goes:** to your subscription server over an encrypted (HTTPS) connection. It is not linked to your name or other personal identity.
- **On device:** the identifier is stored locally to keep it stable between app restarts.

### 2.2 Crash reports and usage statistics (Yandex AppMetrica)

- **What:** crash reports and non-fatal error reports (error type and stack trace), anonymized product events (e.g., VPN connect/disconnect result, subscription update success/failure — **without** server addresses, subscription names, or your HWID), and standard technical metadata (device model, OS version, app version, language, timezone).
- **Why:** to detect and fix failures and to understand which features are used.
- **Where it goes:** processed by Yandex AppMetrica according to the [AppMetrica terms and privacy documents](https://appmetrica.io).
- **Your control:** the "Send analytics" switch in the App's side menu disables sending crash reports and events. It is enabled by default and can be turned off at any time.

### 2.3 Advertising data (Yandex Mobile Ads)

- **What:** advertising identifiers and technical device data required to deliver ads.
- **Why:** the App shows interstitial ads (after VPN disconnection) and rewarded ads ("Support the developer"). This keeps the App free.
- **Where it goes:** processed by Yandex advertising services according to the [Yandex privacy policy](https://yandex.com/legal/confidential/).

### 2.4 Local data

Settings, server configurations, subscription links, VPN credentials (usernames/passwords/keys of your servers), routing profiles, and log files are stored **only on your device**. They are never sent to the Developer. VPN credentials are passed only to the local V2Ray/Xray core to establish your connection.

## 3. What We Do NOT Collect

- The content of your VPN traffic, browsing history, or DNS queries made through the tunnel. The App functions as a client: traffic is encrypted end-to-end and is not readable by the App.
- Your name, email address, phone number, or contacts.
- Precise location.

## 4. Permissions

- **Camera** — used only for scanning QR codes when you add a server or subscription. The camera is never used in the background.
- **Notifications** — used to inform you about background subscription update results.
- **Storage access** — used to import/export configuration files and geo database files used by the V2Ray/Xray core.

## 5. Data Sharing

We do not sell your data. Data is shared only with the processors described above:

| Processor | Purpose | Data |
| --- | --- | --- |
| Your subscription server (chosen by you) | Subscription updates | HWID (`X-HWID` header) |
| Yandex AppMetrica | Crash reports, anonymized analytics | Device/app metadata, events, crash data |
| Yandex Mobile Ads | Ad delivery | Advertising identifiers, device data |

**App log file (`app.log`, stored only on your device):** the App records subscription update diagnostics — subscription names, mirror hosts, and failure reasons (HTTP status/timeout). For subscriptions marked "encrypted" by you, hosts and URLs are never written to the log; only the subscription name and the type of failure are recorded. You can view and clear this log anytime (Logs screen).

All network communication uses encrypted (TLS) connections.

## 6. Data Retention and Deletion

- **Local data:** deleted when you uninstall the App.
- **Analytics:** retained according to AppMetrica's standard retention terms; you can stop collection at any time via the "Send analytics" switch.
- **HWID on your subscription server:** managed by the operator of that server. To request deletion, contact your subscription provider; for subscriptions operated by the Developer, email [imsel.vpn@gmail.com](mailto:imsel.vpn@gmail.com).

## 7. Children

The App is not directed at children under 13, and we do not knowingly collect data from children under 13.

## 8. International Transfers

Your data may be processed in countries where the processors described above operate (including Russia). Applicable safeguards are described in the processors' privacy documents.

## 9. Changes to This Policy

We may update this Privacy Policy. The current version is always available within the App ("About" dialog) and in the App's documentation. Continued use of the App after changes take effect constitutes acceptance of the updated policy.

## 10. Contact

Questions or data-related requests: [imsel.vpn@gmail.com](mailto:imsel.vpn@gmail.com)

See also: [Terms of Service](terms-of-service.md)
