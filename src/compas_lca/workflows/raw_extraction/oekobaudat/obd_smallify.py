"""
Keep only rows for selected UUIDs from a semicolon CSV (preserving rows verbatim).
Configure everything in the CONFIG section below (no argparse, no terminal input).

This script is for testing, or if you want to extract only a speicific UUID
(in case the OBD gets updated, you would not have to extract all entries, and only
the new entries/UUIDs).

Make sure to simplify the OBD first with obd_simplify.py
"""

from pathlib import Path
import random

# =========================
# CONFIG — edit these only
# =========================
INPUT_PATH  = Path("data/lca_database/OBD_samples.csv")      # path to your big OBD CSV
OUTPUT_PATH = Path("data/lca_database/OBD_samples_gemini3_rerun.csv") # path to write the reduced OBD CSV

"""
Choose how UUIDs are selected:
   - "manual" : only MANUAL_UUIDS
   - "random" : only RANDOM_COUNT randomly sampled UUIDs (seeded with RANDOM_SEED), for testing
"""
SELECT_MODE = "manual"  # "manual" | "random"

"""
When SELECT_MODE == "manual", choose whether to keep only MANUAL_UUIDS,
or subtract them (i.e., keep everything except MANUAL_UUIDS).
"""
MANUAL_POLICY = "subtract"      # "keep" | "subtract"

# Manually chosen UUIDs to keep (optional)
MANUAL_UUIDS = [
    '0acfd20e-f1ec-490b-a1cc-86bfffe85ac2',
    '1c681356-2541-43e7-b1d4-9c4d0a936a08',
    '161e1abd-fe38-45f6-8658-8bf4fa88eb7c',
    '05057e7f-0522-4091-8148-75033a5755ab',
    '03ed395a-bc7b-4287-9013-8ba3ac1a2900',
    '0bc73361-b7cf-4901-a7a8-926238ff2874',
    '127a23f5-d954-41c9-8f8a-ecca18aca691',
    '04a73d83-f4cb-4d8d-8ca5-60535784d198',
    '1b0a3488-9b02-4c98-b421-8c746d350f97',
    '1dd31347-9ece-44c5-8a84-5dc1595d6ae4',
    '26353b00-6cd3-426d-903b-9fc5b1670398',
    '211df162-f205-4314-b14b-32c5e51a2de9',
    '069a6b40-aa11-4f66-b385-ea9f5cc2a91e',
    '215cd9f5-391f-4d3b-8d83-277253a49038',
    '23fc083c-960d-4d31-a509-f383e01c3179',
    '2582642e-308a-4a8e-b731-3289665b44da',
    '1c610d47-8371-4a68-9b0d-b79a36f9c588',
    '02c77d20-8370-47db-8c30-a448a290ebc9',
    '227f2f83-68aa-4a12-9ce1-48fbc709b897',
    '19ca78fb-6c45-4e47-9d20-0abc601fb306',
    '09e1332a-b73f-4c7e-a698-4b9b5b40f4f4',
    '16fe3d1d-c950-483c-92ac-32564803dd8c',
    '2753664c-01fe-4962-933f-5663f5b10f8d',
    '0cd05abb-52fd-4b29-9190-a7a94a856254',
    '1901cc08-5f7d-4170-81d1-cfbb84ebd31e',
    '143a4df2-563e-4ef9-b75b-90e1cf9f7ef9',
    '17bcb2ce-39fd-400b-baf9-370c63589efd',
    '06c6f44f-dc14-4095-8e3e-7e483eccf50c',
    '0f2f2410-d9e2-4e0f-837a-987cb3186d81',
    '0b87961e-ea66-4757-b483-229ece59cb97',
    '1549fb80-44c7-42b3-a806-124206bff53d',
    '24b673e5-b737-4fe9-ab51-ca68391ccdd3',
    '1c01243d-fd22-4655-bfaf-484dc024d620',
    '0dec19c7-53db-4cb9-bbba-4d44d3da62a9',
    '07ba7069-57a8-45a9-af66-2c51dadda7c0',
    '17b2f191-4208-491b-9d98-b944da09020f',
    '01f45a03-460d-4e55-b5c9-72d3e8eda18e',
    '17563d7b-443c-4c1b-84f9-27026241c0b9',
    '2771022c-bf7d-4b54-85c2-5a04b75cb231',
    '268829ec-c8d9-4c6e-abdd-542acc494dd1',
    '0d61ff01-935e-4934-befe-cb0b2ea18187',
    '004f3f4e-5bb8-4d9e-a104-6999a9e8ad5b',
    '2812667f-8ca5-4ee1-a9ac-7ed13045b7ff',
    '0293b4f2-e2cb-466b-bb53-bd4505aa5138',
    '00485255-d8a7-4e6d-b2ab-fba929e3cc4a',
    '15ec902a-44f0-4d3e-9d5a-e3ccb09397ba',
    '1018517a-1fb0-40c9-aa82-d7d3c2687b49',
    '5b8126fe-6d23-4a60-95b1-0fb75b343398',
    '7d689ee1-891f-4b2e-8775-57800526735e',
    '4a85b86c-bcf7-40c7-b9dd-8621aef94eb4',
    '37a63555-2ac1-45e8-b802-6d947f30b99a',
    '91935678-1a09-43e0-8a84-294522407ac3',
    '2b389c60-468e-4f3e-abfa-f279262ecd5d',
    '2cdcffc6-84e9-4238-b8af-beebabea9a2d',
    '30514538-fcb4-483b-b5d5-c108d2037536',
    '55c43440-f4ca-4221-8995-6cd00e3e99da',
    '2a814fa2-bd7f-4a2f-a08d-30b8b2f06c73',
    '5c536009-b0a8-4539-86c2-c3b8247f7f1a',
    '49151a25-7935-49a4-beca-4422b158c405',
    '7ac6fad2-61fb-42a2-9993-54c044ae8b38',
    '514d0f56-13d8-45a3-9267-01be064d6ce3',
    '2aca59c3-5947-43ca-af88-e6ae6366ce3f',
    '7b69e7b4-68dd-49a3-b2dc-ae608b66eece',
    '432e4b39-301e-4154-ac8a-ac635d6c36ad',
    '755a481d-a74b-4ba0-b417-cc26767b2d50',
    '6869f7c1-1b2b-4f30-afc9-823a0104f1d9',
    '7110e1a5-c072-4e2d-90d4-812650019e5a',
    '43b998a6-a505-4044-acbc-e7f52cd8facb',
    '591b693f-8cfe-41fc-877d-68c730d9c31d',
    '4b42a944-ff7e-4540-a46b-c21074255143',
    '72952cc7-9e13-44b0-8e9f-a0d514a9482e',
    '56b3f121-be89-4ac7-9c2e-5cea671e586b',
    '45e6dcac-70b9-4982-bf04-4ff566facba1',
    '6c46fc8d-6a74-415b-8e6b-b90af72178ac',
    '4b3adfcf-18b6-43fd-ad5b-ff9781bc081f',
    '4dbf5c48-7445-4fdb-be1f-94614ce872fa',
    '68bcc8d5-b1ab-4e30-89b6-e1bb586faa62',
    '7f39809a-407d-41cc-b0e7-c7e67faff54b',
    '82c533fa-7117-4101-a286-d2d7c207e696',
    '8d704158-8c85-49d0-97a6-9a9ea51c3a89',
    '7a7e7ba5-ede9-4592-bd47-b0cc072d7602',
    '592ffe6e-4c21-4a24-ba67-273acbfca373',
    '8e46a65c-1862-4628-8031-66a71a7e4679',
    '50968665-1e8f-42d5-953b-e100364dad60',
    '9009b594-ee3d-4d2e-b8d9-e0a4bffabad7',
    '835b163b-3a44-4c9f-9fb8-9a2beb20d520',
    '905fe012-538c-4b01-ba47-3be9a0dd8c5f',
    '6d963c68-07fc-48ab-92ae-c011b5ff6f00',
    '75985e7f-7ec3-4a74-9877-9b84c2cf89cd',
    '28bd87f7-6a55-481f-9725-01a94e5ed8ce',
    '42c7b8f7-40ce-4d1e-93ca-b0e779889c40',
    '78b0d28b-3fe2-463a-825c-9af8e4548e23',
    '8aef9045-4b5f-4362-954f-2edda71f63e6',
    '671be705-dd34-47ff-ade2-9a86bab074ac',
    '2bd4c91f-16e5-4e01-b8b5-0c01aac363ce',
    '8d51f336-2546-4fde-8f04-1e7738d47e41',
    '766ea5bd-3f0f-4d48-a399-9c4a372524d8',
    '5845e582-d877-44c2-a8a7-f5c5ef3a6463',
    '881736f8-1bb1-4e9f-852a-cc9a1f676343',
    '7aba3603-0689-4da5-8d24-fd92ae398d07',
    '86138863-3c1c-4345-9ae9-03ba28a5f9a7',
    '3d80fcc7-bc1a-42d1-b792-db2ff85f2417',
    '8c4eb262-9ae6-4ace-8f3d-0b06f2007f3e',
    '69787b5c-495c-409f-bc5b-58af0dc39e56',
    '33c70403-553e-442c-ac5b-0ee86cceffd6',
    '397c2798-c713-4fe1-9a9c-f597317e7998',
    '8231f9c8-fedd-46f5-aaf0-bd302324718b',
    '414d0e5b-7628-466c-89d3-56e107b60aa6',
    '7180425d-0e35-47f5-84d9-cbf39486b411',
    '76c44e98-da73-4111-b5d7-80a5c8617e03',
    '8f11c179-e367-4833-93f3-10597923c79c',
    '83fae93c-605a-449c-8508-525ea1bc58ba',
    '92ddc155-28e8-44d5-8e15-b7475f5d6872',
    '2e60360a-61f1-4d86-a537-a50a3d4165ba',
    '64318385-991b-4aec-83a4-99c59f6f2471',
    '355dbd58-78dc-45cc-be8a-43d66d117e15',
    '8f6daa87-b2ee-4eb0-95e0-737ac8c6a59f',
    '457c1f80-8ca9-451d-a552-36479fc8113c',
    '4b97b317-87d0-4b03-92cc-d38178f2d5e7',
    '5541250a-f8d8-4c67-9f24-47ab54686c30',
    '732dcc2d-1131-4a75-a669-e871675b5ba4',
    '5d087386-ed6b-4786-b37b-87164384927b',
    '3abc810c-ef3a-4ab4-b6d8-0217716e213e',
    '86d919ee-8f30-4ca4-9b7e-717aecba6ac0',
    '4c009f04-44e1-42e3-a32e-4929294debab',
    '7c0535db-e6d1-4342-871d-74cde862d97a',
    '7f453b20-5b30-4707-bf43-32e2d07a51f9',
    '7395adfa-2a3f-43f1-be88-5d4a392968a5',
    '83514986-e053-4b4b-9570-c04f37babb24',
    '50d421e2-3a7b-4659-92a4-f20d6a52fcf0',
    '7091503e-34e5-44cd-9acb-7c2f16f6097f',
    '4f0df91e-dbc6-457b-bdd9-bf6ca0b518d3',
    '52d4092b-b220-4850-9179-4f11094da94e',
    '51fa051b-38fb-422f-96e2-b2ee6e6f9445',
]




# When SELECT_MODE uses random
RANDOM_COUNT = 2
RANDOM_SEED  = 6  # set to None for unseeded randomness
# =========================


def first_field(line: str) -> str:
    """
    Extract the first field (UUID) without parsing the rest, to preserve the line verbatim.
    Assumes the UUID is the first field and fields are delimited by ';'.
    """
    idx = line.find(";")
    if idx == -1:
        # No delimiter found; return the entire (stripped) line as the UUID candidate
        return line.strip("\r\n")
    return line[:idx]


def main() -> None:
    # Read all lines as-is. newline="" prevents Python from altering line endings.
    with INPUT_PATH.open("r", encoding="latin1", newline="") as f:
        lines = f.readlines()

    if not lines:
        print("Input file is empty.")
        return

    header = lines[0]
    data_lines = lines[1:]

    # Collect distinct UUIDs in file order
    uuids = []
    seen = set()
    for line in data_lines:
        if not line.strip():
            continue
        u = first_field(line)
        if u and u not in seen:
            seen.add(u)
            uuids.append(u)

    # Build selection
    selected = set()

    if SELECT_MODE == "manual":
        manual_set = set(MANUAL_UUIDS)

        if MANUAL_POLICY == "keep":
            selected.update(manual_set)
        elif MANUAL_POLICY == "subtract":
            # In subtract mode, we keep everything EXCEPT the manual UUIDs.
            # We construct 'selected' as the complement relative to UUIDs present in the file.
            selected.update(u for u in uuids if u not in manual_set)
        else:
            raise ValueError(
                f"Invalid MANUAL_POLICY: {MANUAL_POLICY!r}. Must be 'keep' or 'subtract'."
            )

    elif SELECT_MODE == "random":
        pool = uuids
        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)
        if RANDOM_COUNT > len(pool):
            raise RuntimeError(
                f"RANDOM_COUNT={RANDOM_COUNT} exceeds available pool size {len(pool)}."
            )
        selected.update(random.sample(pool, RANDOM_COUNT))

    else:
        raise ValueError(f"Invalid SELECT_MODE: {SELECT_MODE!r}. Must be 'manual' or 'random'.")


    # Final sanity checks
    if not selected:
        raise RuntimeError(
            "No UUIDs selected. Adjust SELECT_MODE / MANUAL_UUIDS / RANDOM_COUNT."
        )

    # Warn for any manual UUIDs not present
    if SELECT_MODE == "manual":
        missing = [u for u in MANUAL_UUIDS if u not in seen]
        if missing:
            print("WARNING: These manual UUIDs were not found in the input CSV:")
            for u in missing:
                print(f"  {u}")


    print(f"Keeping {len(selected)} UUID(s):")
    for u in selected:
        print(f"  {u}")

    # Filter lines: keep header + any data line whose first field (UUID) is selected
    kept = [header]
    kept_count = 0
    for line in data_lines:
        if not line.strip():
            continue
        u = first_field(line)
        if u in selected:
            kept.append(line)  # append original line verbatim
            kept_count += 1

    # Write output (verbatim lines)
    with OUTPUT_PATH.open("w", encoding="latin1", newline="") as f:
        f.writelines(kept)

    print(f"Wrote {kept_count} row(s) (+ header) to: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()