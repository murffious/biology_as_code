#!/usr/bin/env python3
"""Fed vs overnight fast — pathway regulation activities (open FLOW)."""

from biology_as_code import fed, overnight_fast, pathway_activities

if __name__ == "__main__":
    print("Fed:", pathway_activities(fed()))
    print("Overnight fast:", pathway_activities(overnight_fast()))
