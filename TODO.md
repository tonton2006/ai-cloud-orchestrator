# GCP Cloud Orchestrator - TODO

## Phase 2: Production IAM Setup (Before Boomi Rollout)

### Current State (Phase 1)
- ✅ SSH key metadata support implemented
- ✅ Works for testing and individual use
- ⚠️ Keys are passed as parameters and stored in VM metadata
- ⚠️ No centralized access control or audit trail

### Required for Production (Phase 2)

#### 1. Implement OS Login
Replace SSH key metadata approach with Google Cloud OS Login for IAM-based SSH access.

**Benefits:**
- IAM-based access control (grant/revoke via IAM policies)
- Automatic SSH key management using Google account keys
- Full audit trail in Cloud Logging
- Supports 2FA/MFA through Google accounts
- Team-friendly (each user uses their own Google identity)

**Implementation Tasks:**
- [ ] Enable OS Login API for project
- [ ] Update `create_instance` to enable OS Login on VMs via metadata
- [ ] Add firewall rules for SSH if needed
- [ ] Update documentation for team onboarding
- [ ] Test with multiple team members' Google accounts
- [ ] Create IAM policy templates for SSH access

**Reference:**
- https://cloud.google.com/compute/docs/oslogin
- Enable OS Login: `gcloud compute project-info add-metadata --metadata enable-oslogin=TRUE`
- Grant access: `gcloud compute instances add-iam-policy-binding VM_NAME --member=user:USER_EMAIL --role=roles/compute.osLogin`

#### 2. Implement Firewall Rule Management
Add tools to manage GCP firewall rules programmatically.

**Use Cases:**
- Opening Minecraft port 25565
- Opening web server ports (80, 443)
- Custom application ports

**Implementation Tasks:**
- [ ] Add `create_firewall_rule` tool
- [ ] Add `delete_firewall_rule` tool
- [ ] Add `list_firewall_rules` tool
- [ ] Implement security best practices (least privilege, IP allowlisting)

#### 3. Enhanced get_instance_details
Currently returns empty dict. Implement to return:
- [ ] External IP address
- [ ] Internal IP address
- [ ] Instance status (RUNNING, STOPPED, etc.)
- [ ] Machine type and specs
- [ ] Disk information
- [ ] Metadata (including SSH configuration)
- [ ] Network tags

#### 4. Security Hardening
- [ ] Implement service account best practices
- [ ] Add secret management for sensitive data (not in plain text tokens)
- [ ] Token auto-refresh mechanism
- [ ] Rate limiting and quota management
- [ ] Error handling improvements for IAM permission issues

#### 5. Documentation & Team Onboarding
- [ ] Create team setup guide for OS Login
- [ ] Document IAM roles and permissions needed
- [ ] Add troubleshooting guide
- [ ] Create example workflows for common tasks
- [ ] Add architecture diagrams

## Priority

**High Priority (Before Boomi Demo):**
- OS Login implementation
- Firewall rule management
- Enhanced get_instance_details

**Medium Priority:**
- Security hardening
- Documentation

---

**Last Updated:** 2025-10-16
**Owner:** Tony Glass
**Target:** Before Boomi team rollout
