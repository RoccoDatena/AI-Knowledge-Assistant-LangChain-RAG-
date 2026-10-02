# Terraform future setup

Terraform files are intentionally not provisioned yet. This directory only
records the future infrastructure boundary for the portfolio project.

Planned principles:

- separate development and production environments;
- remote state with locking when a team workflow is introduced;
- least-privilege IAM;
- encrypted storage;
- secrets outside Git;
- variables for every provider, region, and resource size;
- `terraform plan` reviewed before every apply;
- explicit destroy procedure and budget alarms.

No AWS resource is created by the current repository.
