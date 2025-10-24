#!/usr/bin/env python3
"""Professional Deployment with Automatic Checkpoints"""

import sys
import subprocess
from pathlib import Path
from time import time

# Import professional utilities
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.rollback_manager import rollback_manager

logger = get_logger(__name__)

def deploy_with_checkpoints(phases_to_deploy=None):
    """Deploy infrastructure with automatic checkpoint creation"""
    
    start_time = time()
    logger.info("Professional deployment started", event_type="professional_deployment_started")
    
    try:
        # Create pre-deployment checkpoint
        pre_checkpoint = rollback_manager.create_checkpoint("Pre-deployment checkpoint")
        logger.info(f"Pre-deployment checkpoint created: {pre_checkpoint}")
        
        # Get phases to deploy
        if not phases_to_deploy:
            phases_dir = Path(__file__).parent.parent / 'phases'
            phases_to_deploy = sorted(phases_dir.glob('*.yaml'))
        
        deployed_phases = []
        failed_phases = []
        
        for phase_file in phases_to_deploy:
            phase_name = phase_file.stem
            phase_start_time = time()
            
            logger.deployment_started(phase_name, 1)
            
            try:
                # Deploy phase (simplified - in real implementation would use CloudFormation)
                result = subprocess.run([
                    'aws', 'cloudformation', 'deploy',
                    '--template-file', str(phase_file),
                    '--stack-name', f'ial-{phase_name}',
                    '--capabilities', 'CAPABILITY_IAM'
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    phase_duration = time() - phase_start_time
                    logger.deployment_completed(phase_name, 1, phase_duration)
                    deployed_phases.append(phase_name)
                    
                    # Create checkpoint after successful phase
                    checkpoint_id = rollback_manager.create_checkpoint(f"After {phase_name} deployment")
                    logger.info(f"Phase checkpoint created: {checkpoint_id}", phase=phase_name)
                    
                else:
                    logger.deployment_failed(phase_name, result.stderr)
                    failed_phases.append(phase_name)
                    
                    # Auto-rollback on failure
                    logger.warning(f"Phase {phase_name} failed, initiating auto-rollback")
                    rollback_success = rollback_manager.auto_rollback_on_failure(phase_name, result.stderr)
                    
                    if rollback_success:
                        logger.info("Auto-rollback completed successfully")
                    else:
                        logger.error("Auto-rollback failed")
                    
                    break  # Stop deployment on first failure
                    
            except subprocess.TimeoutExpired:
                logger.deployment_failed(phase_name, "Deployment timeout (10 minutes)")
                failed_phases.append(phase_name)
                break
                
            except Exception as e:
                logger.deployment_failed(phase_name, str(e))
                failed_phases.append(phase_name)
                break
        
        # Final summary
        total_duration = time() - start_time
        
        if failed_phases:
            logger.error(
                f"Deployment failed after {len(deployed_phases)} successful phases",
                deployed_phases=deployed_phases,
                failed_phases=failed_phases,
                total_duration=total_duration,
                event_type="professional_deployment_failed"
            )
            return False
        else:
            logger.info(
                f"Deployment completed successfully: {len(deployed_phases)} phases",
                deployed_phases=deployed_phases,
                total_duration=total_duration,
                event_type="professional_deployment_completed"
            )
            
            # Create final checkpoint
            final_checkpoint = rollback_manager.create_checkpoint("Post-deployment checkpoint")
            logger.info(f"Final checkpoint created: {final_checkpoint}")
            
            return True
            
    except Exception as e:
        logger.error(f"Deployment process failed: {e}", exc_info=True)
        return False

def main():
    """Main deployment entry point"""
    
    success = deploy_with_checkpoints()
    
    if success:
        print("✅ Professional deployment completed successfully")
        sys.exit(0)
    else:
        print("❌ Professional deployment failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
