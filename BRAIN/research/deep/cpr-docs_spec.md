# Custom rings

A custom ring enforces your own compliance rules on private transfers in the Solana Privacy Program (SPP). The ring program moves a ring note only after it verifies the proofs and approvals its settings demand. Ring RPC proves, co-signs, pays for and sends wallet operations, and a wallet can also prove and send its own. This document describes each control, who can change it, what each party is trusted with, and the decisions behind them.

The docs form one ladder from this overview down to the code. Each rung says only what the rung above cannot.

1. This spec: the controls, components, roles, trust, flows and decisions.
2. Design notes, one short file for each concept that is hard to see from here: [records and roots](design/records-and-roots.md), [owner rails](design/owner-rails.md), [the record writer](design/record-writer.md), [co-signing](design/co-signing.md), [privacy](design/privacy.md), [audit and recovery](design/audit-and-recovery.md), and [proof composition](design/proof-composition.md).
3. Exact sub-specs: [hashing](spec/crypto/hashing.md), [envelope](spec/crypto/envelope.md), [disclosure](spec/crypto/disclosure.md) and [public inputs](spec/crypto/public-inputs.md).
4. Component READMEs, the interface contracts and operator setup: [repository](../README.md), [Storage program](../programs/storage/README.md), [Ring RPC](../services/ring-rpc/README.md) and [TypeScript SDK](../sdk-libs/ts/README.md).
5. Code comments, the invariant at each check.

## Compliance Rules

1. ZK Policy
   1. Allowlist
   2. Blocklist
   3. Frozen list
   4. Asset allowlist
   5. Outflow limits per transfer
   6. Auditor
2. Ring account controls
   1. Pause
   2. Permanent delegate
   3. Co-signer approval
3. Ring RPC
   1. Readers
   2. Co-signer limits

## 1. ZK Policy

The policy defines which checks a transfer must prove. `Initialize` pins the first rule table, and the policy authority then sets the rule table and signs the list entries. A rule screens the sender, every output owner or every asset, and rules join with AND. A rule is a grant, met by presence on any of its grant lists, or a denial, met by absence from its one deny list. The program refuses three rule forms. A rule that reads several lists by absence fails with `MultiListAbsenceRule`. A rule that reads a grant list by absence or a deny list by presence fails with `InvertedListPolarity`. A rule that mixes presence with absence fails with `MixedPolarityRule`. Each denied list therefore takes its own rule. A list has no effect until a rule reads it. A new rule table binds at once, and every proof made under the old one fails. A ring created without a rule table never gets one. [Records and roots](design/records-and-roots.md)

### 1.1. Allowlist

An allowlist is a list of approved identities. A rule can require the sender, every recipient, or both, to be on it. A recipient rule screens every output, the sender's change and each exit included, and the owner of each withdrawal. A guard can exempt payments at or below a threshold, so only recipients above it must be listed. The threshold is one value for the rule, compared with each owner's total of each asset, or one value per asset in the asset's record. Change that the sender's own ring notes fund adds no receipt.

### 1.2. Blocklist

A blocklist is a list of identities or assets the ring refuses. A sender rule over it stops every transfer of a blocked identity. Its notes stay in the ring, it can still merge them, and the delegate can still move them. A blocklist refuses known members only. A fresh key passes it.

### 1.3. Frozen list

The frozen list is a second authority list, kept apart from the blocklist. A sender rule over it stops every transfer of a frozen identity. A merge and a delegate move read no rule. The private frozen list is its salted counterpart. It holds enrolled owners under salted keys, and a rule reads it as its own deny list.

### 1.4. Asset allowlist

An asset rule over the allowlist admits only listed assets to deposits and transfers. A guard on that rule can admit small amounts of other assets. A deposit runs the owner and asset rules on each recipient and asset, and no sender rule, because a depositor spends no note.

### 1.5. Outflow limits per transfer

An asset's record can hold a cap and a co-sign bound. The transfer proof keeps each owner's charged outflow of the asset at or below the cap. It sets the `OUTFLOW` approval bit when a charged outflow passes the co-sign bound. An asset with no record has neither, and a ring with no own records bounds no outflow. An owner's net outflow is its actual decrease, `debit`. Its charged outflow adds `charge`, a share of what leaves the ring beyond every owner's debit. The two differ only when an owner's spend returns to it while something else leaves in the same transaction.

Per asset `a`, over the sender rows `j` in ascending owner identity order:

```text
held_j     = row j's live inputs of a, default-ring notes included
returned_j = row j's live ring outputs of a
leaving    = every exit of a, whoever receives it, + the gross public withdrawal of a
debit_j    = max(held_j - returned_j, 0)               net outflow
kept_j     = held_j - debit_j
H = sum held_j, T = sum debit_j, K = sum kept_j
D          = min(leaving, H) - min(leaving, T)
R_j        = kept_0 + ... + kept_j
share_j    = floor(D * R_j / K), D on the last row, share_-1 = 0
charge_j   = share_j - share_(j-1)
charged_j  = debit_j + charge_j                        charged outflow
```

`D` is at most `K`, and `K = 0` forces every charge to zero. Each charge is `floor(D * kept_j / K)` or one more, the charges sum to `D` exactly, and no charge passes `kept_j`. The row order alone places a rounding unit, and no prover input picks a share. The gross public withdrawal subtracts no deposit. An asset with no live ring output is bound over its debits, since no row keeps it.

`leaving` names no payer. A transaction that composes independent payments can therefore charge an owner for an exit or a withdrawal another party funds. The charge stays within what that owner kept. Payments in separate transactions never charge each other. The SDKs report each owner's charge before signing, so a caller can split such payments.

As an example, A spends 100 of an asset and receives 100 back in a ring output. B deposits 100, and the transaction withdraws 100 in public. A's net outflow is 0 and its charged outflow is 100. A cap of 100 proves and a cap of 99 refuses. The charge is intended.

Limits over time are Ring RPC's, see 3.2. Differs from the PR 15 draft: per-transfer outflow limits live in the transfer proof. [Co-signing](design/co-signing.md)

### 1.6. Auditor

The auditor holds the ring's viewing key. It reads the tokens, amounts and owners of every transfer, deposit and merge, and on an anonymous ring the hidden sender. Every operation carries a proof that the auditor can open it. The auditor can't move funds. [Audit and recovery](design/audit-and-recovery.md)

## 2. Ring account controls

Differs from the PR 15 draft: the ring account holds the keys of these controls, not a separate program config. SPP's ring config holds the pause flag.

### 2.1. Pause

Pausing stops all activity in the ring until it's resumed: deposits, transfers, withdrawals, merges and delegate moves. Funds stay where they are. Record updates, policy changes and other controls still run.

### 2.2. Permanent delegate

A permanent delegate is a key that can move any note of the ring without its owner's signature. The admin and the delegate set it once, on any ring kind. A delegate move transfers within the ring and withdraws, and takes no deposit leg. SPP has no exit selector on its authority rail, so a delegate move sends no output to the default ring. It reads no rule, guard, cap or approval, so a blocked or frozen member's funds move. Its nonzero-key inputs still match their owners' tracking rows, its outputs still meet the output key rule, and its records still open to the auditor. On an anonymous ring the delegate is public, and the source and the recipients stay hidden. SPP opens the ring's authority rail at creation on a pool with permissionless ring activation, and SPP governance opens it on any other pool.

The permanent delegate of a Token-2022 mint signs the same move for a transfer whose every input and output is of that mint. It needs no ring delegate. Ring RPC builds its proofs and returns it no nullifier secret.

### 2.3. Co-signer approval

A co-signer is a key that the co-signer admin designates to approve selected operations. Each co-signer has its own account and scope. A transaction carries a co-signer for each demanded class, and one co-signer may cover several classes. The program refuses a co-signer that covers no class still uncovered, and a hidden sender cannot approve itself. The co-signer on its own cannot move funds. Differs from the PR 15 draft: co-signer approval is enforced by the ring program, and only its limits live in Ring RPC.

#### Operations that can require approval

- **`TRANSFERS`**: a transfer that spends a note. A frame with `no_spend` set, a merge and a delegate move never demand it.
- **`DEPOSITS`**: a deposit, and a transfer with a deposit leg.
- **`WITHDRAWALS`**: a transfer with a public withdrawal.
- **`APPROVE_OUTFLOW`**: an owner's charged outflow of an asset above the asset's co-sign bound, see 1.5.
- **`APPROVE_WITHDRAWAL`**: the gross withdrawn of an asset, with no deposit subtracted, above the asset's withdrawal threshold. It reads no owner and limits what a transaction withdraws in public, whoever funds it.

The first three demand a co-signer only when the ring configured a co-signer of that class. The proof sets the two approval bits in `approval_mask`. A set bit demands its approver whether or not the ring configured one, so it fails closed without one. A delegate move sets no bit.

## 3. Ring RPC

### 3.1. Readers

A reader accesses decrypted activity through Ring RPC without holding the auditor key. The policy authority grants access across the ring. A wallet grants access to its own activity, and its own key reads nothing without that grant. A deployment keeps every grant in one store, the ring's storage tree or Ring RPC's encrypted database. Differs from the PR 15 draft: one store per deployment, never both.

### 3.2. Co-signer limits

Ring RPC co-signs only within limits the policy authority writes to each asset's record:

1. **Sender limit:** what one sender outputs to another owner or another ring and withdraws of the asset within a window. A deposit does not lower it.
2. **Volume limit:** what the ring transfers, takes in and pays out of the asset within a window.
3. **Deposit and withdrawal limits:** what the ring takes in and pays out in public deposits and withdrawals, each with its own window.

These limits bind only the operations the ring requires co-signing for. Ring RPC enforces them when it decides whether to co-sign, and the ring program checks only that the co-signer signed. Ring RPC refuses to co-sign an operation that moves an asset with no record. Enforcement at co-signing follows the PR 15 draft's Flow 9 and trust assumption 3. A limit binds every operation of a class, for example Transfers, only when Ring RPC is the one co-signer that covers that class. Otherwise a transfer below the co-sign bound, or one that another co-signer signs, can pass uncounted. The per-transfer cap and co-sign bound of 1.5 hold either way. Differs from the PR 15 draft: limits are set per asset, not per co-signer (open question 1).

## Components and ownership

1. **Ring program:** one deployment per ring. Verifies the ring proofs and controls, then calls SPP signed by its ring PDA.
2. **Storage program:** one shared deployment. Keeps the root history of policy record trees, each under one authority, and of each ring's tracking tree. It verifies the proof of each tree update and of each first enrollment. It checks no policy.
3. **Ring RPC:** our hosted service. Holds the auditor key, writes policy records, applies enrollments, relays and pays for wallet operations, co-signs under limits, merges enrolled owners' notes and serves readers. It opens every enrolled owner's sealed secret from the ring's tracking rows.
4. **Ring indexer:** projects every policy and tracking tree from confirmed blocks and lists pending enrollments. It serves record and tracking openings, and forwards every other call to Photon.
5. **Ring prover:** the zolana prover with the ring circuits added.
6. **SDKs and CLI:** the Rust and TypeScript SDKs build ring operations. A wallet sends them through Ring RPC by default, or reads the records and Merkle paths from the ring indexer, proves and sends them itself. The operator CLI creates, deploys and governs rings.

Zolana owns SPP: its programs, its circuits and its rails. Those circuits are audited, and this repository never refactors them. The ring imports zolana gadgets unchanged and keeps its own copy of any gadget it must change. A new SPP circuit enters zolana as new files only.

The ring uses these SPP rails:

1. **Confidential signer rail:** each input owner signs the Solana transaction.
2. **Confidential in-proof rail:** the owner signs inside the proof of SPP's anonymous rail, and public co-owners can sign the transaction beside it. SPP hides the owner, and the ring statement publishes it as the sender.
3. **Anonymous rail:** a hidden owner signs inside the SPP proof, with optional public co-owners who sign the transaction. Under the frame's `PUBLIC_OWNERS` flag no hidden owner exists, every live owner is a published signer, and SPP's confidential rail settles the frame.
4. **Authority rail:** the ring PDA moves notes with no owner signature, for the delegate, on a confidential and on an anonymous ring.
5. **Ring merge.** A deposit is a transfer on the signer rail, or under `PUBLIC_OWNERS` on an anonymous ring, that spends no note.

An in-proof owner on ring transfers lets Ring RPC pay for and send a confidential transfer from one wallet signature. Zolana's own in-proof circuit serves default-ring transfers only, so the confidential in-proof rail proves on SPP's anonymous rail. Both confidential owner rails stay. [Owner rails](design/owner-rails.md)

## Accounts

1. **Ring account:** one per ring. Holds the roles, the mode, the auditor key, the delegate, the co-signer counts and the policy. It binds the addresses of the ring's tracking registry, of its records tree and of its one curator tree. A ring without a policy, anonymous included, may bind no records tree.
2. **Co-signer account:** one per co-signer, holding its key and its scope.
3. **Storage registry:** one per policy record tree, owned by the Storage program. Holds the authority, the grace period, the next leaf, the immutable ring id, the immutable tracking registry pin, the tracking floor and the root history. Record contents live in instruction data and the ring indexer. A nonzero ring id makes the tree that ring's own records. A zero ring id makes it a curator only. Any registry can serve as a curator, the ring's own records included. A nonzero pin names the one tracking registry whose enrolled owners the registry can hold salted entries for. `Initialize` and `UpdatePolicy` refuse a salted source that pins no tracking registry or another one before they store a policy. A refused write changes nothing. A frame that reads a salted list refuses such a source again.
4. **SPP ring config:** owned by SPP at the ring PDA. Holds the activation, pause and authority-rail flags.
5. **Tracking registry:** one per ring, owned by the Storage program and created by `Initialize`. Holds the immutable ring id, the immutable auditor key, the next leaf as a `u64` and the root history of the ring's enrollments. Its tree has `TRACKING_QUAD_HEIGHT = 16` levels of four, so it holds `TRACKING_CAPACITY = 2^32` leaves. [Tracking](design/records-and-roots.md#tracking)
6. **Tracking authorization:** one per owner per tracking registry, owned by the Storage program. Holds the owner's nullifier key, list tag, viewing key and ephemeral key, and whether an apply inserted the owner's row. Its ciphertext seals the nullifier secret and the list salt to the auditor. The tracking leaf holds the member, the next member, the nullifier key, the ciphertext hash and the list tag, and no viewing key.
7. **Owner grant:** one per owner, tracking registry and reader, owned by the Storage program. Holds whether a program owner grants that reader access to its activity.

A transfer or deposit passes the ring account and the tracking registry. It adds the records registry when it reads the policy or the thresholds, and the curator registry when the policy uses a curator source. It adds a co-signer account for each co-signer the demanded classes need. The program checks each registry against the address the ring account binds and reads its roots live. Differs from the PR 15 draft: the config and the policy are one account, and no roots are synced into it. A storage tree is a root history over an indexed tree, not account compression. [Records and roots](design/records-and-roots.md)

## Authorities

Five on-chain roles govern a ring. Every role key is nonzero once set, and no key holds two roles.

1. **Admin:** hands the admin, policy, pauser or co-signer admin role to a new key, which also signs. It appoints the delegate once.
2. **Policy authority:** sets the policy and signs the authority record updates: authority lists, mint settings and limits, ring-wide reader grants and list approvals.
3. **Pauser:** pauses and resumes the ring.
4. **Co-signer admin:** creates, rescopes and closes co-signer accounts.
5. **Delegate:** moves any note of the ring outside the rules. Set once, never rotated.

The upgrade authority deploys the program. Among ring instructions it signs only `Initialize`, which names the four role keys. Before that it can request the auditor key and the records tree from Ring RPC. Differs from the PR 15 draft: its single Config Authority splits into these roles.

Ring RPC keeps one key file per role. The auditor key opens ring activity. The service key signs auditor key releases, and every signed read and grant binds it. The storage authority signs record tree updates. The co-signer signs co-signatures. The fee payer pays for relayed transactions. The grant rows key seals database reader grants. Each key does one job. Ring RPC refuses to start when two role files hold the same secret, and its root secret yields auditor keys only.

## Trust Assumptions

1. **Storage authority:** trusted for every policy record. The tree proof verifies the update, not the record. A write the authority signs directly skips every Ring RPC check, the wallet's signature included. No authority writes a tracking tree, so none can delay, change or clear an enrollment.
2. **Policy authority:** trusted to set policy rules, lists, limits and ring-wide grants, and to bind the records. Each other role is trusted for its own control.
3. **Ring RPC:** trusted to protect the auditor key and every proof input a wallet hands it. It is trusted to enforce reader grants and co-signer limits, and to write records as signed. A depositor or the delegate signs the message Ring RPC builds. The ring SDKs sign it only when the quoted fee payer pays and the one instruction is the ring operation the request asked for. With derived keys Ring RPC relays and pays only for a ring whose config names an auditor key it derives, and its rate limits bound what it pays. Replicas share the store and the same service, auditor and co-signer keys. One projection lease owns each ring, and one writer serves each storage authority. Ring RPC holds the auditor key, so it opens the nullifier secret of every enrolled owner and links that owner's spends. Only a note under the zero nullifier key carries no secret, and its sender and the auditor both compute its nullifier.
4. **Curator:** a ring trusts the authority of its one curator tree.
5. **Delegate:** trusted with every member's funds. It moves and withdraws any note of the ring outside the rules, guards, caps and approvals.
6. **Upgrade authority:** trusted to create the ring and to deploy upgrades that keep the program's guarantees. An upgrade can replace every check. Only the operator tools refuse an upgrade over a ring account the new release cannot read.
7. **Key generator:** the ring proving keys come from a single-party setup. Whoever ran it could forge every ring proof.
8. **Revocation timing:** a restrictive update binds on chain the moment the Storage program applies it. A transaction that passed Ring RPC or a relayer before then fails on chain. The apply proof marks an update restrictive when it tightens a list, guard or bound, writes a private list or changes an asset limit. A curator's revocation binds as fast as its authority writes it.
9. **Limits:** Ring RPC enforces co-signer limits only on what it co-signs. A co-signer outside Ring RPC enforces none.
10. **Photon, ring indexer and chain RPC:** Photon and the ring indexer that forwards to it are trusted for complete history, the chain RPC for confirmed contents. A balance read observes the service's verified finalized history. No authoritative balance or limit decision reads it, see [reading through Ring RPC](design/audit-and-recovery.md#reading-through-ring-rpc). Ring RPC verifies each record opening under the newest root. While the ring indexer lags that root, Ring RPC's tree-mode reader grant checks, its limit updates and its co-signatures on a deposit, transfer or withdrawal fail.
11. **SPP governance:** trusted to activate the ring and to open its authority rail when SPP does neither at creation.
12. **Delegate message:** before the delegate signs, the ring SDKs open the message's output records and check the move against the request. Each requested payment must match its output kind, owner key, nullifier key, mint and amount. Each ring record must be sealed to its owner's viewing key. Each withdrawal must match its recipient, mint, amount and token program. Every other ring output must return to a requested source. The message carries no deposit, extra leg or data. The published nullifiers of notes the delegate opened for the requested sources must number `R`, the proven count of spent notes. The SDKs do not choose which of those notes the move spends. A mint's permanent delegate states its mint and opens no source, so its check holds only the outputs. An unrequested wallet's notes of that mint may fund the move it signs. It learns the notes of that mint Ring RPC selects for any wallet it names.

## Glossary

| # | Term | Type | Definition |
| --- | --- | --- | --- |
| 1 | **Ring note** | UTXO | An SPP note tagged with the ring's id. Only a transaction the ring program signs moves it. |
| 2 | **Default ring** | Note set | SPP notes outside every ring. An exit pays into it. |
| 3 | **Ring account** | Account | The one account that holds a ring's roles, settings, policy and the addresses of its record trees. |
| 4 | **Mode** | Ring setting | A `RingKind`: `AuditOnly`, `Policy`, `Anonymous` or `AnonymousPolicy`. Fixed at creation. Setting a delegate changes no mode. |
| 5 | **Policy ring** | Ring setting | A ring with a rule table. Every transfer proves it inside its one ring proof. An audit-only ring proves the same statement with the policy section switched off. |
| 6 | **Member record** | Tree leaf | One member's list bits and, for an asset, mint settings, in a policy registry. |
| 7 | **Mint settings** | Record fields | An asset's guard threshold, cap, co-sign bound, withdrawal threshold and window limits. |
| 8 | **Records** | Storage tree | The ring's own record tree. |
| 9 | **Curator** | Storage tree | A record tree of any authority that serves some of a ring's lists. A ring has at most one. |
| 10 | **Revision** | Root number | The sequence number of a storage root. A proof names its root by revision, and the program reads that root live from the registry. |
| 11 | **Rail** | Transfer form | How SPP authorizes a spend: owner signer, in-proof owner, hidden owner or delegate. |
| 12 | **Exit** | Output | An output paid to the default ring. Its owner is public. |
| 13 | **Public leg** | Transfer part | A SOL or SPL deposit or withdrawal inside a transfer. Its account, asset and amount are public. |
| 14 | **Enrollment** | Tracking row | An owner's fixed nullifier key, list tag and ciphertext hash in the tracking tree. The authorization account holds its current viewing key and sealed secret and salt. `RegisterKey` proves the seal. It lets the auditor link that owner's spends and lets Ring RPC merge its notes and serve the delegate. |
| 15 | **Record update** | Signed request | A signed list of record writes that Ring RPC queues and applies. |
| 16 | **List approval** | Record update | A wallet's policy record update that waits for the policy authority to set the lists it needs. It is separate from enrollment. |
| 17 | **Relay** | Ring RPC operation | Ring RPC proves, co-signs, pays for and sends an operation the wallet requested. |
| 18 | **Shape** | Proof width | The input and output counts of a transfer. SPP has one proving key per shape, and a ring key serves every shape up to its input class. |
| 19 | **Wallet** | User | Holds spending keys and authorizes transfers of its ring notes. |
| 20 | **Reader** | User | Uses granted read access to query decrypted ring activity through Ring RPC. |
| 21 | **Auditor** | Authority | Holds the auditor key and decrypts ring transfers, deposits and merges. It also decrypts each enrolled owner's sealed nullifier secret and list salt. |
| 22 | **Co-signer** | Authority | Signs operations when the ring's co-signer scopes or outflow bounds demand it. |
| 23 | **Delegate** | Authority | Moves any note of the ring with no owner signature and outside the rules. |
| 24 | **Policy authority** | Authority | Sets the ring's rules, lists, mint settings and ring-wide grants. |
| 25 | **Storage authority** | Authority | Signs the updates of one record tree. Ring RPC holds it for the ring's records. |
| 26 | **Upgrade authority** | Authority | Deploys and upgrades the ring program and signs `Initialize`. |
| 27 | **Auditor stream** | Ciphertext | One AES-256-CTR stream per transfer, sealed to the auditor key and proven. It carries the transaction viewing secret, the note count, the entry records on an entry key and each published slot's recipient key. |
| 28 | **Output record** | Ciphertext | One per published slot, the slot's kind, amount, owner key, mint, nullifier key and blinding, sealed to the recipient key the sender supplies. The proof holds it to the slot's commitment. A non-exit slot's body carries it, and an exit's travels in the auditor message. |
| 29 | **Change** | Output | An anonymous output to the sender. It leads the slots under a zero tag, and its record is sealed to the sender's own viewing key. |
| 30 | **Sender bundle** | Ciphertext | One per anonymous transfer, encrypted to the sender's viewing key. It holds the output seed and each slot's recipient key. No proof constrains it. |
| 31 | **Reply metadata** | Ciphertext | An optional unauthenticated claim about the sender, one fixed length per frame. |
| 32 | **Published slot** | Output position | An output position below the frame's count `m`. A compact frame omits every later position. |
| 33 | **Tracking registry** | Storage tree | One ring's tree of enrollments. Any applier moves pending enrollments into it, and no authority writes it. |
| 34 | **Tracking floor** | Registry field | The highest tracking revision a private write proved a row under. A frame that reads a salted list through the registry names no lower tracking revision. |
| 35 | **Note count** | Envelope field | The sealed count `R` of spent notes among the published inputs. The proof names no note position. |
| 36 | **Payload** | Ciphertext | A non-exit slot's data hashes and application data past its record, under the frame's `HAS_DATA`. No proof constrains it. |

## Flows

1. Enrollment and list approval
2. Record updates
3. Deposit
4. Transfer (anonymous, confidential, exit to the default ring, withdrawal)
5. User merge
6. Managed merge
7. Authority transfer
8. Reader access grants and revocation
9. Co-signer limits configuration

## 1. Enrollment and list approval

Every owner that spends a ring note under a nonzero nullifier key enrolls on the ring's tracking registry, on every ring kind. A sender may pay an owner under any nonzero key, and the note spends only once that key is the owner's enrolled one. A note under the zero nullifier key needs no row for its key. A wallet has one nullifier secret, so enrollment discloses it to each ring's auditor it enrolls with. An owner's nullifier key, list tag and ciphertext are final on one registry after the first enrollment.

1. **Owner:** signs an enrollment write off chain with its nullifier key, its list tag, its viewing key, an ephemeral key and a ciphertext. The ciphertext seals its nullifier secret and list salt to the ring's auditor key, and a `RegisterKey` proof shows the seal. The owner sends no transaction and pays nothing.
2. **Enrollment writer:** the holder of the ring's `EnrollmentWriter` role verifies each write and its proof, batches the held writes, and sends ring `EnrollBatch` behind an Ed25519 precompile instruction carrying every owner signature. The ring calls Storage `ApplyEnrollments` as `ring_auth`. Ring RPC is that writer for the rings its operator names, under a key none of its other jobs uses, and within the fee budget the operator sets.
3. **Storage program:** reads each owner signature from the precompile instruction, verifies every first enrollment's `RegisterKey` proof against the ring id and the auditor key the tracking registry pins, refuses the zero nullifier key, and applies the batch proof over the entries it computes from the writes.
4. **Ring indexer:** lists pending authorizations, projects the tracking tree and serves its openings.

An enrollment grants nothing until an apply places its row under a tracking root. The owner's notes under its key spend from the first root that holds its row. Before then a salted owner write for it fails. The `EnrollmentWriter` alone sends `EnrollBatch`, and Storage checks every owner signature itself. [Tracking](design/records-and-roots.md#tracking)

A wallet rotates its viewing key per ring. It signs `Enroll` again on that ring's tracking registry with the new viewing key and every other field unchanged. The rotation carries no proof, and the program refuses a change to any other field. The rotation moves only the authorization's viewing key and waits on no apply. A sender verifies the owner's row under a tracking root and reads the viewing key from the owner's authorization at `confirmed`. An address that carries an older viewing key therefore seals to the current one.

List approval admits a wallet to lists, and it is separate from enrollment:

1. **Wallet:**
   1. Signs a record update for its own lists.
   2. Names the reader list, or the allow or approval list its ring's rules read from its own records, when it awaits one.
2. **Ring RPC:**
   1. Checks the cluster, the signature, the expiry, and that the wallet writes only its own record and its own grant records.
   2. Holds an update pending list approval until the **Policy authority** approves it or refuses it, or its window ends.
3. **Policy authority:** approves a pending update with its own update that sets every awaited list, and both reach the tree in one root.
4. **Ring RPC:** queues the update, proves the tree update, submits it to the **Storage Program**, and pays fees.
5. **Ring indexer:** projects the applied records and serves their openings.

## 2. Record updates

The **Wallet** writes its own viewing flag and its wallet grants. The **Policy authority** writes the authority lists, the mint settings and ring-wide grants.

1. **Wallet or Policy authority:** signs an update for one cluster, ring and tree, valid until a slot, and sends it to **Ring RPC**.
2. **Ring RPC:**
   1. Checks that the signer may write each entry.
   2. Queues wallet and authority updates in separate batches. An update its list approval joined rides first in its approver's batch.
   3. Sends an authority batch at its next pass, and a wallet batch when it is full, aged or ahead of a queued authority update.
   4. Leaves the grace to the **Storage program**. The apply proof marks a batch [restrictive](design/records-and-roots.md#root-history) when it tightens a list, guard or bound, writes a private list or changes an asset limit. Such a batch retires every earlier root. Any other batch keeps the outgoing root for the grace period, and over a full history it evicts the oldest kept root.
   5. Proves a batch with salted owner writes under the private apply key. The proof opens each such owner's applied row under one root of the pinned tracking registry. It holds the written key to the owner's salted member under a salt that opens the row's list tag. A wrong salt fails the proof. The update names that root's revision. The Storage program reads the root and raises the registry's tracking floor to the revision in the same instruction. A batch whose salted owner has no applied row fails before the proof.
   6. Refuses a queued authority update once its signer no longer holds the policy role.
   7. Proves each batch and submits it, paying fees.

[The record writer](design/record-writer.md)

## 3. Deposit

A deposit moves SOL or tokens from a wallet's public balance into up to 8 ring notes. The token and amounts are public. It is a transfer that spends no note, every SPP input a dummy, funded by a deposit leg.

**Limit:** one deposit carries at most 3 distinct tokens, the public slots of a transfer key. The SDKs refuse a wider deposit before proving, and the wallet splits it.

1. **Wallet:**
   1. Chooses the token, amount and recipient.
   2. Prepares the deposit notes and seals one record per note.
   3. Sends the deposit request to **Ring RPC** on the deposit relay rail. The funder signs a text that names the cluster, the Ring RPC service, the ring, the funder, each leg's mint and amount, and `deposit_request_digest`, the SHA-256 of `"zolana/ring-rpc-relay-deposit"` and the proof input bytes. No owner signs.
2. **Ring RPC:**
   1. Checks that the ring is active. Refuses a frame with a real input, with two funders, with the fee payer as funder, or with a signature the funder did not make.
   2. Generates the transfer proof. It shows the owner and asset rules hold for each recipient and asset. It also proves each zero-key recipient absent at the accepted tracking root.
   3. Returns the transaction to the **Wallet** for signing.
3. **Wallet:** the funder signs the transaction to authorize the SOL or SPL token transfer.
4. **Ring RPC:**
   1. Co-signs when deposits demand approval.
   2. Pays fees and submits the deposit to the **Ring Program**.
   3. Follows the deposit to confirmation. The recipient's **Wallet** finds its notes by view tag.

Without Ring RPC the **Wallet** reads the records itself, generates the transfer proof, and pays for and submits the deposit.

On every ring each note's record names its owner key, and the transfer proof binds that key to the note's owner commitment. No ring instruction signs SPP's proofless ring deposit.

## 4. Transfer

A unified flow for anonymous and confidential transfers, exits and withdrawals. On every rail the transfer proof holds each live input to the rail's owner rule. It holds each live ring input under a nonzero key to its owner's tracking row. The proof seals the count `R` of spent notes and names no note position. The auditor classifies each published nullifier from its own note index, and `R` checks the count. Each output's record is sealed to the recipient key the sender supplies.

**Variants:**

1. **Anonymous:** a hidden owner signs inside the SPP proof, and public co-owners can sign beside it. The sender and recipients stay hidden from chain observers. No proof constrains a payload, a non-exit tag or the sender bundle, and SPP's external data hash binds their bytes. The discovery guarantee is [Discovery](spec/crypto/disclosure.md#discovery). A sender can attach reply metadata, and a recipient reads it as an unauthenticated claim.
2. **Confidential:** the policy screens the sender and recipients as public inputs. The wallet signs inside the proof, and the signer rail serves one or more owners who send their own transaction.
3. **Exit to the default ring:** some outputs leave the ring to a public owner.
4. **Public withdrawal:** SOL or SPL transfers to one or more accounts, optionally alongside other outputs. On the anonymous rail every withdrawal pays one key. Ring RPC can create the missing token account of an SPL withdrawal.

**Steps:**

1. **Wallet:** takes a quote that names the fee payer and builds the transfer from its own notes. It seals the **Auditor** stream, signs the SPP message hash and sends the proof inputs to **Ring RPC**. It reads no Merkle path and no record.
2. **Ring RPC:**
   1. Verifies the owner's signature.
   2. Reads the required member records and Merkle paths.
   3. Generates the SPP proof and the ring proof.
   4. Co-signs within the limits when the transfer demands a co-signer.
   5. Pays fees, submits the transaction to Solana and follows it to confirmation.

A recipient wallet finds an anonymous note by scanning ring history, see [wallet scanning](design/audit-and-recovery.md#wallet-scanning). Without Ring RPC the **Wallet** does step 2 itself and pays from a fee payer it chooses. A demanded co-signer still signs. On the anonymous rail a co-signer must differ from the hidden owner. The payer, a funder, another signer or an exit may name the hidden owner, and such a party exposes it. The SDKs refuse that by default, and a caller can waive it.

A frame publishes `m` output slots up to the key's capacity, and omits the rest as a suffix. A ring output publishes no owner identity, and an exit's owner is public. Every ring program transaction is one inline v1 transaction, with no frame buffer and no lookup table. The SDKs refuse before proving a frame whose transaction passes 4,096 bytes or 64 addresses, or whose SPP CPI data passes 10 KiB. The key catalog in `program-libs/interface/src/proof/key_catalog.rs` fixes each key's input class. The SDKs refuse a wider shape as unkeyed, and the sender merges first. A relayed transfer carries withdrawals only, and a relayed deposit takes the deposit relay rail of [Deposit](#3-deposit). A transfer that spends a note beside a deposit leg goes out in the owner's own transaction, and on an anonymous ring its payer funds the leg.

The table names construction paths, subject to policy, key capacity and frame fit. Direct SDK paths build their own proofs. Hosted paths ask Ring RPC to prove and submit. Public co-owners still sign the transaction. A missing proving key refuses every path.

| Transfer combination | Direct Rust | Direct TypeScript | Hosted Ring RPC | Proof and program boundary |
|---|---|---|---|---|
| Confidential signer, ring or default-ring inputs, optional public co-owners | Yes | Yes | No signer path | SPP verifies public owner signatures. Default-ring inputs select an entry key. |
| Confidential in-proof owner, ring inputs, optional public co-owners | Yes | Yes | Yes | SPP verifies the owner's proof signature and each public co-owner's transaction signature. |
| Confidential in-proof owner with a default-ring input | Refused | Refused | Refused | The ring entry proof permits the input, but the SDK paths refuse it. |
| Anonymous hidden owner, ring inputs, optional public co-owners | Yes | Yes | Yes | Input zero belongs to the hidden owner. Its key is nonzero. Public co-owners sign. |
| Anonymous entry, 