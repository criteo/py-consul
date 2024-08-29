import json

from consul.callback import CB


class Txn:
    """
    The Transactions endpoints manage updates or fetches of multiple keys
    inside a single, atomic transaction.
    """

    def __init__(self, agent) -> None:
        self.agent = agent

    def put(self, payload):
        """
        Create a transaction by submitting a list of operations to apply to
        the KV store inside of a transaction. If any operation fails, the
        transaction is rolled back and none of the changes are applied.

        *payload* is a list of operations where each operation is a `dict`
        with a single key value pair, with the key specifying operation the
        type. An example payload of operation type "KV" is
        dict::

            {
                "KV": {
                  "Verb": "<verb>",
                  "Key": "<key>",
                  "Value": "<Base64-encoded blob of data>",
                  "Flags": 0,
                  "Index": 0,
                  "Session": "<session id>"
                }
            }
        """
        return self.agent.http.put(CB.json(), "/v1/txn", data=json.dumps(payload))
