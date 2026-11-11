# Pre-Send Check — Nothing Internal Goes Out

Feature note for the Cloudgentic Gateway (open source) and the Cloudgentic Cloud
service (the commercial deployment layer inside AgentForge / cloudgentic-cloud).
Recorded by Aldo Grillo, 2026-11-11. Logged as idea #2 in the "Business Ideas -
Project Ideas" sheet.

## The problem

AI assistants write emails and documents on behalf of a human. Drafts are not
always polished or public-ready: they can carry internal working material —
notes between the AI and the human, instructions, meta-commentary, placeholders,
or personal data that was never meant for the recipient. If the assistant sends
without a check, internal content can go out the door. (Origin: 2026-11-11,
after an AI-drafted reply was sent, the founder had the exact sent text read
back from the Sent folder to confirm nothing internal was in it. That manual
read-back should be a system check instead.)

## The feature

Before any outgoing email or document is sent through the gateway, the gateway
runs a pre-send check on the final content:

- No internal notes or AI-to-human working content (instructions, reasoning,
  meta-commentary, draft scaffolding) in a message addressed to a recipient.
- No personal or sensitive data that should not leave (beyond what the
  recipient is meant to receive).
- No leftover placeholders or unfinished draft markers.
- The message reads as finished and public-ready.

The system checks upon itself, at the one place every send must pass through:
the gateway.

## Why it belongs in the gateway

- The AI (e.g. Muse) does NOT connect directly to the user's email. It
  connects once to Cloudgentic, and the gateway sits between the AI and the
  user's accounts (Gmail, Calendar, Slack, and the other connected services).
- The gateway can manage multiple Google accounts for one user (e.g. a personal
  Gmail and a Workspace account). Whichever account a send goes out on, the
  gateway runs the check first.
- Existing market pieces are adjacent, not this: DLP tools (Microsoft Purview,
  Google Workspace DLP, KnowBe4 Prevent) pattern-match sensitive data types;
  Itzal checks content at the moment before send, aimed at data leakage;
  editorial checkers (e.g. ContactMonkey ConfidenceCheck) review polish for
  internal newsletters. None of them check an AI assistant's own outgoing work
  product for internal AI-to-human content at the agent gateway.

## Rollout (founder's go-to-market)

1. Ship it in the open-source gateway first. People who need it adopt it and
   customize it; that is the funnel.
2. The cloud version (Cloudgentic Cloud) is the destination: hosted, managed,
   and the only route on phone, where running a local gateway would need a
   connector. Desktop users can run the open-source gateway locally; the cloud
   version is the easy place it all connects.
3. Put real work into the gateway overall — several main features working
   integrated, with genuinely customized open-source parts people need — so a
   share of open-source users convert to the cloud service.

## Status

Idea recorded 2026-11-11. Not yet specced for build.
