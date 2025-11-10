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
INPUT_PATH  = Path("data/lca_database/OBD_2024_I_A2.csv")      # path to your big OBD CSV
OUTPUT_PATH = Path("data/lca_database/OBD_2024_I_A2_test.csv") # path to write the reduced OBD CSV

"""
Choose how UUIDs are selected:
   - "manual" : only MANUAL_UUIDS
   - "random" : only RANDOM_COUNT randomly sampled UUIDs (seeded with RANDOM_SEED), for testing
"""
SELECT_MODE = "random"  # "manual" | "random"

# Manually chosen UUIDs to keep (optional)
MANUAL_UUIDS = [
    '004f3f4e-5bb8-4d9e-a104-6999a9e8ad5b',
    '04ffd29d-1cd0-46d2-8971-ea6cb956484a',
    '06c6f44f-dc14-4095-8e3e-7e483eccf50c',
    '07ba7069-57a8-45a9-af66-2c51dadda7c0',
    '0a1fa7f9-ad49-4942-a173-cb8c4ad99c9b',
    '0cb92770-9007-48c6-bc03-466af8894419',
    '0cd05abb-52fd-4b29-9190-a7a94a856254',
    '0f2f2410-d9e2-4e0f-837a-987cb3186d81',
    '1018517a-1fb0-40c9-aa82-d7d3c2687b49',
    '14a64935-b4d9-4442-be5c-f1adf6042c6d',
    '1549fb80-44c7-42b3-a806-124206bff53d',
    '15fb59fb-085b-4d66-9240-d098e4724112',
    '19c8f194-c3ab-4797-9b1a-8f1788bf12d8',
    '1c22a17e-aca4-4126-9fde-f02c33aa741e',
    '1fe648df-fd53-4231-b43d-fcf26b20978a',
    '215cd9f5-391f-4d3b-8d83-277253a49038',
    '22527f3b-5985-41a7-8028-655142979cfd',
    '2272105e-734d-491d-a36c-d4ba2d759900',
    '227f2f83-68aa-4a12-9ce1-48fbc709b897',
    '236dd4ac-341b-4b66-8acd-785b2ff9b40c',
    '268829ec-c8d9-4c6e-abdd-542acc494dd1',
    '27f20dc1-5529-4194-8a06-1ae5b7ba6a51',
    '28a26228-4acd-4bba-b62c-54a54c35526f',
    '2903adee-32f8-418a-9785-4042afc7d75d',
    '2b389c60-468e-4f3e-abfa-f279262ecd5d',
    '2b58ef09-a4cd-42e3-9f90-08fe6e905211',
    '2bd4c91f-16e5-4e01-b8b5-0c01aac363ce',
    '2cdcffc6-84e9-4238-b8af-beebabea9a2d',
    '2e60360a-61f1-4d86-a537-a50a3d4165ba',
    '30452630-b12d-43bf-b140-58e0db0ba549',
    '30514538-fcb4-483b-b5d5-c108d2037536',
    '3489c0eb-415f-4dc8-8c2d-b276f6efebc6',
    '35a5da15-d24b-44a7-b816-80085e47ccd1',
    '35f6a697-d1a9-402f-9bc8-1e6a29d21b71',
    '375d08fb-c1e8-4b37-886f-e91d9e29b135',
    '397c2798-c713-4fe1-9a9c-f597317e7998',
    '3abc810c-ef3a-4ab4-b6d8-0217716e213e',
    '3e15eb88-e824-4a81-972a-45e06930aa19',
    '3f764d2e-320b-4996-8c28-0f38e8971044',
    '3feca796-791b-46d3-8160-95ef243ffb9d',
    '408815ac-3893-4913-8c9c-16753a643388',
    '422b2446-8a3f-457d-b47b-4728b2869d86',
    '430bc64e-bda6-44bb-87f0-53c2dbe562cf',
    '432e4b39-301e-4154-ac8a-ac635d6c36ad',
    '4a213dd2-6651-4125-b808-2a7ff2a69a96',
    '4b42a944-ff7e-4540-a46b-c21074255143',
    '4bd628c6-0a1f-466a-a09a-cafe514a900b',
    '4dadfb92-ba5d-48de-bb7b-394c28911a90',
    '50d97298-1f18-404d-b94d-cef5d28f944c',
    '5541250a-f8d8-4c67-9f24-47ab54686c30',
    '55a6caa5-0c2f-410f-b752-f78e20ed93fa',
    '5618a4e7-1f60-4205-9869-30c2e9fad094',
    '56b3f121-be89-4ac7-9c2e-5cea671e586b',
    '5845e582-d877-44c2-a8a7-f5c5ef3a6463',
    '591b693f-8cfe-41fc-877d-68c730d9c31d',
    '61c0c795-7116-407d-8635-68fe422f76a9',
    '621a52d8-4cad-4f0a-af43-60cebebb3f0c',
    '684a5040-dfd8-4530-973b-17581fcc0f8c',
    '6869f7c1-1b2b-4f30-afc9-823a0104f1d9',
    '699e3d57-72b4-402d-a0ee-cebb06f3cdf1',
    '6b75bee7-b123-423e-acff-1cf446864415',
    '6d963c68-07fc-48ab-92ae-c011b5ff6f00',
    '6fd412c4-dd19-43be-bf4f-cbd2ee0c45ab',
    '732a4fb1-1017-4682-ac12-49a256354964',
    '766ea5bd-3f0f-4d48-a399-9c4a372524d8',
    '77a553ca-357e-4910-b114-5aa912d4d0e2',
    '7a265769-b70e-4cbb-a9ac-f6af4e55f8a6',
    '7a854919-e883-426e-9204-713191b151bd',
    '7aba3603-0689-4da5-8d24-fd92ae398d07',
    '7c828537-8009-4ee4-9ef1-e6fd71d9421f',
    '7e0c008a-009d-4357-92c1-afb2cec3bc0a',
    '82c533fa-7117-4101-a286-d2d7c207e696',
    '83514986-e053-4b4b-9570-c04f37babb24',
    '8476b2c2-29dd-4706-a067-f2dd4caec09e',
    '85e76e87-fc16-4fd5-80ed-a07fa5767f56',
    '86d919ee-8f30-4ca4-9b7e-717aecba6ac0',
    '881736f8-1bb1-4e9f-852a-cc9a1f676343',
    '8941afb6-f909-48de-826c-63a6addc2a79',
    '8c4eb262-9ae6-4ace-8f3d-0b06f2007f3e',
    '8cd435d4-54ad-48c0-8d9e-9015b491bb79',
    '8ef7b1b9-da21-43c9-a7d1-9a14d9dc7bcf',
    '8f11c179-e367-4833-93f3-10597923c79c',
    '92ddc155-28e8-44d5-8e15-b7475f5d6872',
    '9a670d29-efb9-4fde-95ab-182a0b1e7280',
    '9d0f1390-089c-4352-87d0-ff0ea5599b12',
    '9db2875b-1e6e-4940-bf63-953043cfef20',
    'a71e60a5-b64b-4715-ae8a-c8c8819149d2',
    'a7c7dd86-4cbe-487c-89f9-1bdd8ebdabec',
    'aab0ed28-e5b0-43d6-a932-4cdc4770c518',
    'aeab0f39-5eab-422f-8c4b-822bb98aa63c',
    'b38aee07-bc49-4c3d-9c34-7e7787255707',
    'b513a7f4-a689-4d5e-8efd-349fb25d21cb',
    'ba11346b-51c7-40cb-8e87-d8bd7ce97c3e',
    'bb838307-4509-4d98-864a-6cb96aaa39a6',
    'bd7ae84e-54c4-4dee-bf0e-8c22cecbcf75',
    'c0915390-0e80-4253-9345-71fd83ef3c99',
    'c4293a12-5023-4e57-bdcd-9b52fbfa6a58',
    'c4ddfdbc-ee2b-4dd5-a754-b317cf06470a',
    'c5982fc9-a486-4f00-82a2-59985d8ab196',
    'c6f77799-ed43-4ec4-bfc3-0759e41b60ca',
    'c8f1d599-b130-4ea0-b0fb-9da088e7c061',
    'c916ceb3-a44d-40b7-8984-861afa589956',
    'c93da4c3-94c9-4c86-b092-610cf1cf012f',
    'cc0d7baa-755a-4a4a-baf3-4fe53d68a041',
    'cc7fcddd-8dcd-4a08-a04b-e7f64c93afa5',
    'ccee13d3-1e5b-41e2-a867-0d844ee6c1bf',
    'd01e5acf-291b-4a5a-8c57-8bc3b11614c4',
    'd688250d-3cfd-40f3-bac7-b19522d2984d',
    'd6f982e3-beda-49f0-a298-694fcbf3ba38',
    'd8f28c30-9229-44c0-b4ae-5a425c542d89',
    'dca9f05c-036b-40e5-ae81-c957c2420fd8',
    'dce28570-db4a-4997-a05c-1fa0d75201c8',
    'ddc96ae4-086c-4033-9e45-c5589f1661ba',
    'deae7522-47b9-47a8-b9a3-176db7c250ae',
    'e131431f-4d99-4d7a-ae0a-744a06de3524',
    'e298e69e-ec22-4c73-b643-7444520133a4',
    'e3d7a045-ee91-43ac-8fb4-a5216c65ba0b',
    'e45e2b55-a8c4-4037-bc7d-e3718c4e28f3',
    'e8cf2935-ef5c-40db-a819-953a9ef12df8',
    'eac26381-2980-47d5-9dc8-b4ea188f9cd4',
    'ed391263-0e6d-43dd-ad3e-43607545f281',
    'eea7e352-bf1d-4e6d-9029-689d7936e6a7',
    'efe61c5a-ff60-4c5c-ba33-8b2dc2a4523a',
    'f0eaf61a-7561-4140-b860-a2e658dbb9c0',
    'f2bf3e4b-10c5-4233-b475-6a8bd6092769',
    'f57ae3ed-2d49-4a71-bfae-fc55e00a4bec',
    'f9f40b59-268d-4a0b-8c80-d978ac97608f',
    'fdbe82c6-7073-4f8c-a540-c37a6bf16cd6',
    'fde18fdc-ca6b-41d3-9918-aab96177fc24',
]

# When SELECT_MODE uses random
RANDOM_COUNT = 2
RANDOM_SEED  = 27  # set to None for unseeded randomness
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
        selected.update(MANUAL_UUIDS)

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