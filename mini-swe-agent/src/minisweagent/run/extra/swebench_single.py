"""Run on a single SWE-Bench instance."""

import traceback
from pathlib import Path

import typer
import yaml
from datasets import load_dataset

from minisweagent import global_config_dir
from minisweagent.agents.interactive import InteractiveAgent
from minisweagent.config import get_config_path
from minisweagent.models import get_model
from minisweagent.run.extra.swebench import (
    DATASET_MAPPING,
    get_sb_environment,
)
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import logger

from datetime import datetime

app = typer.Typer(add_completion=False)

ATTACK_PATH = global_config_dir / "attack"

# fmt: off
@app.command()
def main(
    subset: str = typer.Option("lite", "--subset", help="SWEBench subset to use or path to a dataset", rich_help_panel="Data selection"),
    split: str = typer.Option("dev", "--split", help="Dataset split", rich_help_panel="Data selection"),
    instance_spec: str = typer.Option(0, "-i", "--instance", help="SWE-Bench instance ID or index", rich_help_panel="Data selection"),
    model_name: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "-c", "--model-class", help="Model class to use (e.g., 'anthropic' or 'minisweagent.models.anthropic.AnthropicModel')", rich_help_panel="Advanced"),
    config_path: Path = typer.Option( global_config_dir / "swebench.yaml", "-c", "--config", help="Path to a config file", rich_help_panel="Basic"),
    environment_class: str | None = typer.Option(None, "--environment-class", rich_help_panel="Advanced"),
    exit_immediately: bool = typer.Option( False, "--exit-immediately", help="Exit immediately when the agent wants to finish instead of prompting.", rich_help_panel="Basic"),
    output: Path = typer.Option(None, "-o", "--output", help="Output trajectory file", rich_help_panel="Basic"),
    attack: bool = typer.Option(False, "-a", "--attack", help="Whether to run in attack mode", rich_help_panel="Advanced"),
    attack_id: str = typer.Option(111111, "--attack-id", help="Attack ID (index in the attack directory)", rich_help_panel="Advanced"),
    attack_file: str = typer.Option("vuln.json", "--attack-file", help="Attack File", rich_help_panel="Advanced"),
) -> None:
    # fmt: on
    """Run on a single SWE-Bench instance."""
    dataset_path = DATASET_MAPPING.get(subset, subset)
    logger.info(f"Loading dataset from {dataset_path}, split {split}...")
    instances = {
        inst["instance_id"]: inst  # type: ignore
        for inst in load_dataset(dataset_path, split=split)
    }
    if instance_spec.isnumeric():
        instance_spec = sorted(instances.keys())[int(instance_spec)]
    instance: dict = instances[instance_spec]  # type: ignore
    config = yaml.safe_load(get_config_path(config_path).read_text())
    if environment_class is not None:
        config.setdefault("environment", {})["environment_class"] = environment_class
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class
    if exit_immediately:
        config.setdefault("agent", {})["confirm_exit"] = False
    env = get_sb_environment(config, instance)
    agent = InteractiveAgent(
        get_model(model_name, config.get("model", {})),
        env,
        **({"mode": "yolo", "confirm_exit": False} | config.get("agent", {})),
    )

    exit_status, result, extra_info, problem_statement = None, None, {}, instance["problem_statement"]  # type: ignore[arg-type]
    # extra_info.update(config['model']['model_kwargs'])
    if attack:
        attack_config_path = ATTACK_PATH / instance_spec / attack_file
        attack_config = yaml.safe_load(attack_config_path.read_text())
        extra_info["natural_instruction"] = attack_config["instruction"]
        extra_info["expected_patch"] = attack_config["expected_patch"]
        extra_info["vuln_code"] = attack_config["vuln_code"]
        problem_statement += attack_config["instruction"]
    try:
        exit_status, result = agent.run(problem_statement)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error processing instance {instance_spec}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        if output == None:
            now = datetime.now()
            timestamp = datetime.now().strftime('%m%d-%H%M%S') + f"-{now.microsecond:06d}"
            if attack:
                output = ATTACK_PATH / instance_spec / attack_id / f"{timestamp}.json"
            else:
                output = ATTACK_PATH / instance_spec / "non_attack" / f"{timestamp}.json"
        else: 
            output = output / instance_spec / f"{datetime.now().strftime('%m%d-%H%M%S')}.json"
        save_traj(agent, output, exit_status=exit_status, result=result, extra_info=extra_info)  # type: ignore[arg-type]


if __name__ == "__main__":
    app()
