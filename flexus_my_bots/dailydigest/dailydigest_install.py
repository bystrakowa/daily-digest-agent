import asyncio

from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_bot_install
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_integrations_db
from flexus_client_kit.integrations import fi_google_calendar

from flexus_my_bots.dailydigest import dailydigest_bot
from flexus_my_bots.dailydigest import dailydigest_prompts


TOOL_NAMESET = {t.name for t in dailydigest_bot.TOOLS}

EXPERTS = [
    ("default", ckit_bot_install.FMarketplaceExpertInput(
        fexp_system_prompt=dailydigest_prompts.DIGEST_PROMPT,
        fexp_python_kernel="",
        fexp_allow_tools=",".join(TOOL_NAMESET | ckit_cloudtool.CLOUDTOOLS_QUITE_A_LOT),
        fexp_nature="NATURE_SEMI_AUTONOMOUS",
        fexp_inactivity_timeout=600,
        fexp_description=(
            "Reads newsletters from Gmail, classifies and deduplicates content, "
            "pulls tomorrow's Google Calendar events, and delivers a structured daily digest by email."
        ),
    )),
]

SCHED_DAILY_DIGEST = {
    "sched_type": "SCHED_ANY",
    "sched_when": "WEEKDAYS:MO:TU:WE:TH:FR:SA:SU/19:00",
    "sched_first_question": (
        "It is 19:00 — time to generate and send the daily digest. "
        "Read today's newsletters from Gmail, classify content, pull tomorrow's calendar events, "
        "and send the structured digest to the user's email."
    ),
    "sched_fexp_name": "default",
}


async def install(client: ckit_client.FlexusClient):
    r = await ckit_bot_install.marketplace_upsert_dev_bot(
        client,
        ws_id=client.ws_id,
        bot_dir=dailydigest_bot.DIGEST_ROOTDIR,
        marketable_accent_color="#1A73E8",
        marketable_title1="Daily Digest",
        marketable_title2="Your personal newsletter curator and evening briefing.",
        marketable_author="Flexus",
        marketable_occupation="Newsletter Curator",
        marketable_description=(dailydigest_bot.DIGEST_ROOTDIR / "README.md").read_text(),
        marketable_typical_group="Productivity",
        marketable_setup_default=dailydigest_bot.DIGEST_SETUP_SCHEMA,
        marketable_featured_actions=[
            {"feat_question": "Send me today's digest now", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Update my topic preferences", "feat_expert": "default", "feat_depends_on_setup": []},
        ],
        marketable_intro_message=(
            "Hi! I’m your Daily Digest Agent. Every evening at 19:00 I’ll scan your newsletters, "
            "curate the best content, and send you a structured digest — news, reads, tools, events, "
            "and your meetings for tomorrow. Connect Gmail and Google Calendar to get started!"
        ),
        marketable_preferred_model_expensive="gpt-5.4",
        marketable_preferred_model_cheap="gpt-5.4-nano",
        marketable_experts=[(name, exp.filter_tools(dailydigest_bot.TOOLS)) for name, exp in EXPERTS],
        add_integrations_into_expert_system_prompt=dailydigest_bot.DIGEST_INTEGRATIONS,
        marketable_tags=["Productivity", "Email", "Newsletter", "Calendar"],
        marketable_schedule=[SCHED_DAILY_DIGEST],
        marketable_auth_supported=["gmail", "google_calendar"],
        marketable_auth_scopes={
            "gmail": ckit_integrations_db.GOOGLE_OAUTH_BASE_SCOPES + [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.labels",
            ],
            "google_calendar": fi_google_calendar.REQUIRED_SCOPES,
        },
    )
    return r.marketable_version


if __name__ == "__main__":
    client = ckit_client.FlexusClient("dailydigest_install")
    asyncio.run(install(client))
