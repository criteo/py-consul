from tests.utils import find_recursive


def test_find_recursive():
    ret_value = [
        {
            "AccessorID": "accessorid",
            "CreateIndex": 1,
            "CreateTime": "timestamp",
            "Description": "description",
            "Hash": "hash",
            "Local": False,
            "ModifyIndex": 1,
            "Policies": [{"ID": "id", "Name": "name"}],
            "SecretID": "secretid",
        },
        {
            "AccessorID": "accessorid",
            "CreateIndex": 1,
            "CreateTime": "timestamp",
            "Description": "description",
            "Hash": "hash",
            "Local": False,
            "ModifyIndex": 1,
            "Policies": [{"ID": "id", "Name": "name"}],
            "SecretID": "secretid2",
        },
    ]

    wanted = {
        "AccessorID": "accessorid",
        "Description": "description",
        "Policies": [{"Name": "name"}],
        "SecretID": "secretid",
    }
    wanted2 = {
        "AccessorID": "accessorid",
        "SecretID": "secretid2",
    }
    unwanted = {
        "AccessorID": "accessorid",
        "Description": "description",
        "Policies": [{"Name": "name-ish"}],
        "SecretID": "secretid",
    }

    assert find_recursive(ret_value, wanted)
    assert find_recursive(ret_value, wanted2)
    assert find_recursive(ret_value, [wanted, wanted2])
    assert find_recursive(wanted, wanted)
    assert not find_recursive(ret_value, unwanted)
