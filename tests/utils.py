from __future__ import annotations


def find_recursive(list_or_single_dict: list[dict] | dict, wanted: list[dict] | dict) -> bool:
    """
    Check if the 'wanted' item(s) sub-dictionary structure is/are present in any of the dictionaries in 'list_or_single_dict'.
    'list_or_single_dict' can be either a list of dictionaries or a single dictionary.
    """

    def matches_subdict(haystack: dict, needle: dict) -> bool:
        """
        Check if all key-value pairs in needle are present in haystack.
        This function recursively checks nested dictionaries and lists of dictionaries.
        """
        for key, needle_value in needle.items():
            if key not in haystack:
                return False

            haystack_value = haystack[key]

            if isinstance(needle_value, dict):
                if not isinstance(haystack_value, dict) or not matches_subdict(haystack_value, needle_value):
                    return False
            elif isinstance(needle_value, list):
                if not all(
                    any(matches_subdict(haystack_item, needle_item) for haystack_item in haystack_value)
                    for needle_item in needle_value
                ):
                    return False
            else:
                if haystack_value != needle_value:
                    return False

        return True

    # Turn both args into lists to handle single/multi lookup
    if isinstance(list_or_single_dict, dict):
        list_or_single_dict = [list_or_single_dict]

    if isinstance(wanted, dict):
        wanted = [wanted]

    return all(any(matches_subdict(item, single_wanted) for item in list_or_single_dict) for single_wanted in wanted)
