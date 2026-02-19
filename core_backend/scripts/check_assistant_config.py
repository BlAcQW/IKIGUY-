#!/usr/bin/env python3
"""Check VAPI assistant configuration for warm transfer setup."""
import sys
import json
import requests

def check_assistant_config(assistant_id, api_key):
    """Check assistant configuration."""

    # Fetch assistant data
    response = requests.get(
        f"https://api.vapi.ai/assistant/{assistant_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code != 200:
        print(f"Error fetching assistant: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    print("=" * 70)
    print("ASSISTANT CONFIGURATION CHECK: Hey Papa Hybrid")
    print("=" * 70)
    print()

    # Basic Info
    print(f"Name: {data.get('name')}")
    print(f"ID: {data.get('id')}")
    print(f"Created: {data.get('createdAt')}")
    print(f"Updated: {data.get('updatedAt')}")
    print()

    # Model Configuration
    model = data.get("model", {})
    print("MODEL CONFIGURATION:")
    print(f"  Provider: {model.get('provider')}")
    print(f"  Model: {model.get('model')}")
    print(f"  Max Tokens: {model.get('maxTokens')}")
    print()

    # Tools Check
    tools = model.get("tools", [])
    print(f"TOOLS CONFIGURED: {len(tools)} tool(s)")
    print()

    if tools:
        for i, tool in enumerate(tools, 1):
            print(f"Tool #{i}:")
            print(f"  Type: {tool.get('type')}")

            func = tool.get("function", {})
            print(f"  Function Name: {func.get('name')}")
            print(f"  Description: {func.get('description')}")

            # Check destinations
            dests = tool.get("destinations", [])
            print(f"  Destinations: {len(dests)} destination(s)")
            for j, dest in enumerate(dests, 1):
                print(f"    Destination #{j}:")
                print(f"      Type: {dest.get('type')}")
                if dest.get("type") == "number":
                    print(f"      Number: {dest.get('number')}")
                elif dest.get("type") == "sip":
                    print(f"      SIP URI: {dest.get('sipUri')}")
                print(f"      Message: {dest.get('message')}")
                print(f"      E164 Check: {dest.get('numberE164CheckEnabled', 'N/A')}")

                # Check transfer plan
                plan = dest.get("transferPlan", {})
                if plan:
                    print(f"      Transfer Plan:")
                    print(f"        Mode: {plan.get('mode')}")
                    if "sipVerb" in plan:
                        print(f"        SIP Verb: {plan.get('sipVerb')}")
                else:
                    print(f"      Transfer Plan: Not configured")

            # Check messages
            messages = tool.get("messages", [])
            print(f"  Messages: {len(messages)} message(s)")
            for msg in messages:
                print(f"    - {msg.get('type')}: \"{msg.get('content')[:50]}...\"")
            print()
    else:
        print("  ❌ NO TOOLS CONFIGURED")
        print()

    # Check system prompt for transfer instructions
    messages = model.get("messages", [])
    sys_prompt = ""
    for msg in messages:
        if msg.get("role") == "system":
            sys_prompt = msg.get("content", "")
            break

    print("SYSTEM PROMPT CHECK:")
    if sys_prompt:
        if "transferCall" in sys_prompt:
            print("  ✅ Contains transferCall function reference")
        else:
            print("  ⚠️  No explicit transferCall function reference")

        if "transfer" in sys_prompt.lower():
            print("  ✅ Contains transfer instructions")
        else:
            print("  ⚠️  No transfer instructions found")

        if "complaint" in sys_prompt.lower():
            print("  ✅ Mentions complaint handling")
        else:
            print("  ⚠️  No complaint handling mentioned")

        # Show transfer section
        print()
        print("TRANSFER INSTRUCTIONS FROM SYSTEM PROMPT:")
        lines = sys_prompt.split("\n")
        in_transfer_section = False
        for line in lines:
            if "WHEN TO TRANSFER" in line or "TRANSFER INSTRUCTIONS" in line:
                in_transfer_section = True
            elif line.startswith("###") and in_transfer_section:
                break

            if in_transfer_section:
                print(f"  {line}")
    else:
        print("  ❌ NO SYSTEM PROMPT FOUND")

    print()
    print("=" * 70)
    print("CONFIGURATION SUMMARY:")
    print("=" * 70)

    # Summary
    issues = []
    if not tools:
        issues.append("❌ No tools configured in model.tools")
    else:
        transfer_tool = next((t for t in tools if t.get("type") == "transferCall"), None)
        if not transfer_tool:
            issues.append("❌ transferCall tool not found")
        else:
            print("✅ transferCall tool is configured")

            dests = transfer_tool.get("destinations", [])
            if not dests:
                issues.append("❌ No destinations configured")
            else:
                print(f"✅ {len(dests)} destination(s) configured")

                for dest in dests:
                    if dest.get("type") == "number":
                        print(f"   → Number: {dest.get('number')}")
                    elif dest.get("type") == "sip":
                        print(f"   → SIP URI: {dest.get('sipUri')}")

                    plan = dest.get("transferPlan", {})
                    if plan:
                        print(f"   → Transfer Mode: {plan.get('mode')}")

            messages = transfer_tool.get("messages", [])
            if len(messages) >= 2:
                print(f"✅ Transfer messages configured ({len(messages)} messages)")
            else:
                issues.append("⚠️  Incomplete transfer messages")

    if not sys_prompt or "transfer" not in sys_prompt.lower():
        issues.append("⚠️  System prompt may not have clear transfer instructions")
    else:
        print("✅ System prompt includes transfer instructions")

    print()
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ ALL CHECKS PASSED - Assistant is properly configured for warm transfer")

    print()

if __name__ == "__main__":
    ASSISTANT_ID = "c2854d74-dafe-445c-8c34-1326c2310cb7"
    API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"

    check_assistant_config(ASSISTANT_ID, API_KEY)
