#!/usr/bin/env python3
"""Entry point for the Jira-ServiceNow Agent."""

import sys
import time
import click
from datetime import datetime
from src.config import AppConfig
from src.agent import JiraServiceNowAgent
from src.logger import setup_logging


@click.command()
@click.option('--once', is_flag=True, help='Run once and exit')
@click.option('--schedule', is_flag=True, help='Run on schedule indefinitely')
@click.option('--dry-run', is_flag=True, help='Preview changes without making them')
@click.option('--reset-state', is_flag=True, help='Reset agent state')
def main(once: bool, schedule: bool, dry_run: bool, reset_state: bool):
    """Jira-ServiceNow Automation Agent.

    Fetches update sets from Jira stories and creates parent update sets in ServiceNow.
    """
    try:
        # Load configuration
        config = AppConfig.from_env()
        config.validate_paths()
        logger = setup_logging(config.agent)

        logger.info(f"Initializing {config.agent.name}")
        logger.info(f"Jira: {config.jira.base_url}")
        logger.info(f"ServiceNow: {config.servicenow.instance_url}")

        # Initialize agent
        agent = JiraServiceNowAgent(config)

        # Handle state reset
        if reset_state:
            logger.warning("Resetting agent state")
            agent.state_manager.reset()
            logger.info("State reset complete")
            return

        # Show current state
        logger.info(agent.state_manager.get_summary())

        # Run once
        if once or (not schedule and not reset_state):
            logger.info("Running sync once")
            result = agent.run_once(dry_run=dry_run)
            logger.info(f"Result: {result}")
            agent.cleanup()
            sys.exit(0 if result.success else 1)

        # Run on schedule
        if schedule:
            logger.info(f"Starting scheduled agent with interval {config.agent.run_interval_minutes} minutes")
            interval_seconds = config.agent.run_interval_minutes * 60

            try:
                while True:
                    logger.info(f"Running scheduled sync at {datetime.utcnow()}")
                    result = agent.run_once(dry_run=dry_run)
                    logger.info(f"Next sync in {config.agent.run_interval_minutes} minutes")
                    time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Scheduled agent interrupted by user")
                agent.cleanup()
                sys.exit(0)
            except Exception as e:
                logger.error(f"Fatal error in scheduled agent: {e}")
                agent.cleanup()
                sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
