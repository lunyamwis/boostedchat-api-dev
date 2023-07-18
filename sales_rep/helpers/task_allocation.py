def no_consecutives(allocation):
    """Check that there are no consecutive list items"""
    for i in range(1, len(allocation)):
        if allocation[i] == allocation[i - 1]:
            return False
    return True


def no_more_than_x(allocation):
    """Check that no list item appears more than twice"""
    # import pdb;pdb.set_trace()
    for i in allocation:
        # print(i)

        if allocation.count(i) > 2:
            return False
    return True
