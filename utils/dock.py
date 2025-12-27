import os
import subprocess
from pathlib import Path
import sys
import shlex

def run(cmd):
    """Run a command and return output (stdout + stderr)."""
    print(f"Running: {cmd}")
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout.strip()




def find_image(instance_id):
    print(f"Searching for images containing: {instance_id}")

    images = run("docker images --format '{{.Repository}}:{{.Tag}}'").splitlines()

    candidates = []
    for img in images:
        if instance_id in img:
            candidates.append(img)

    if not candidates:
        print("No image found containing:", instance_id)
        sys.exit(1)

    found = candidates[0]
    print(f"Found image: {found}")
    return found



def prepare_local_dir(instance_id):
    base = Path.home() / "temp_container" / instance_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def create_container(image, instance_id):
    """Create a temporary container."""
    container_name = f"temp_{instance_id}"
    run(f"docker create --name {container_name} {image}")
    print(f"Created container: {container_name}")
    return container_name


def copy_testbed(container_name, local_dir):
    """Copy /testbed from container to local dir."""
    run(f"docker cp {container_name}:/testbed/. {local_dir}")
    print(f"Copied container /testbed → {local_dir}")


def run_in_docker(image, instance_id, command):
    """Run a command in docker with mounted testbed directory."""
    local_path = Path.home() / "temp_container" / instance_id

    docker_cmd = (
        f"docker run --rm -v {local_path}:/testbed -w /testbed {image} {command}"
    )
    output = run(docker_cmd)
    return output


def export_diff(local_dir):
    # Placeholder for future implementation
    pass


def cleanup_local_dir(local_dir):
    """Remove the local directory after agent execution."""
    import shutil
    local_path = Path(local_dir)
    if local_path.exists():
        shutil.rmtree(local_path)
        print(f"🧹 Removed local directory: {local_dir}")


def cleanup_container(container_name):
    """Remove the temp container."""
    run(f"docker rm {container_name}")
    print(f"🧹 Removed container {container_name}")


def process_instance(instance_id):
    # Find image
    image = find_image(instance_id)
    
    # Prepare local dir
    local_dir = prepare_local_dir(instance_id)
    
    # Create container
    container_name = create_container(image, instance_id)

    # Copy /testbed to local
    copy_testbed(container_name, local_dir)

    # Export diff
    export_diff(local_dir)

    # Cleanup container
    cleanup_container(container_name)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pre.py <instance_id>")
        sys.exit(1)

    instance_id = sys.argv[1]

    process_instance(instance_id)
