import urllib.request, json

cases = json.loads(urllib.request.urlopen("http://localhost:5000/api/at_risk?limit=30").read())
print("statuses sample:", [(c["id"], c["status"]) for c in cases[:8]])
for c in cases:
    if c["status"] in ("open", "recovering", "awaiting_payment"):
        eid = c["id"]
        print("trying link for", eid, c["status"], c["amount"])
        req = urllib.request.Request(
            f"http://localhost:5000/api/cases/{eid}/payment_link",
            method="POST",
        )
        try:
            print(urllib.request.urlopen(req).read().decode()[:400])
        except Exception as e:
            body = e.read().decode() if hasattr(e, "read") else str(e)
            print("err", body)
        break
else:
    print("no suitable cases")
