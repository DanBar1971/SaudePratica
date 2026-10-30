# SaúdePrática 1.9.32 · Nearby Connections

Manual, on-device bilateral transfer using Google Play Services Nearby Connections (P2P_POINT_TO_POINT). Both users explicitly authorize sharing all profiles and visually verify the same authentication digits before any files are sent.

The transfer is limited to medication and confirmed/pending intakes, appointments, laboratory/work reports, documents, packaging and identity photos, and non-secret profile fields. It never includes app PIN/keys or deletes local data. For matching records, the local version is authoritative; mismatches are saved under `files/saudepratica_sync_conflicts/` rather than overwritten. Profiles are matched by exact case-insensitive display name, not the `legacy` ID. The archive is temporary in private cache, transferred over Nearby's encrypted connection, and deleted after processing.

Both apps must be open on `Mais → Sincronização familiar`. Select **Tornar visível** on one and **Procurar** on the other, then compare and accept authentication digits on both. Reopen the session to transfer later changes. No unattended/background sync in this version. Test on two phones with a fresh backup before relying on it for clinical data.
