import asyncio
import json
import logging
from pathlib import Path

from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_bot_exec
from flexus_client_kit import ckit_shutdown
from flexus_client_kit import ckit_integrations_db
from flexus_client_kit import ckit_bot_version

logger = logging.getLogger("bot_dailydigest")

BOT_NAME = ckit_bot_version.bot_name_from_file(__file__)
DIGEST_ROOTDIR = Path(__file__).parent

DIGEST_SETUP_SCHEMA = json.loads((DIGEST_ROOTDIR / "setup_schema.json").read_text())

DIGEST_INTEGRATIONS: list[ckit_integrations_db.IntegrationRecord] = ckit_integrations_db.static_integrations_load(
    DIGEST_ROOTDIR,
    allowlist=[
        "gmail",
        "google_calendar",
        "flexus_policy_document",
    ],
    builtin_skills=[],
)

TOOLS = [
    *[t for rec in DIGEST_INTEGRATIONS for t in rec.integr_tools],
]


async def digest_main_loop(fclient: ckit_client.FlexusClient, rcx: ckit_bot_exec.RobotContext) -> None:
    setup = ckit_bot_exec.official_setup_mixing_procedure(DIGEST_SETUP_SCHEMA, rcx.persona.persona_setup)
    await ckit_integrations_db.main_loop_integrations_init(DIGEST_INTEGRATIONS, rcx, setup, need_mongo=False)

    try:
        while not ckit_shutdown.shutdown_event.is_set():
            await rcx.unpark_collected_events(sleep_if_no_work=10.0)
    finally:
        logger.info("%s exit" % (rcx.persona.persona_id,))


def main():
    from flexus_my_bots.dailydigest import dailydigest_install
    scenario_fn = ckit_bot_exec.parse_bot_args()
    bot_version = ckit_bot_version.read_version_file(__file__)
    fclient = ckit_client.FlexusClient(ckit_client.bot_service_name(BOT_NAME, bot_version), endpoint="/v1/jailed-bot")

    asyncio.run(ckit_bot_exec.run_bots_in_this_group(
        fclient,
        bot_main_loop=digest_main_loop,
        inprocess_tools=TOOLS,
        scenario_fn=scenario_fn,
        install_func=dailydigest_install.install,
    ))


if __name__ == "__main__":
    main()
