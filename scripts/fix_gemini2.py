import sqlite3, json
base_url = "https://generativelanguage.googleapis.com"
psd = {"prefix": "mi-gemini", "apiType": "chat", "baseUrl": base_url, "nodeName": "mi-gemini"}
con = sqlite3.connect("data/storage.sqlite")
con.execute("UPDATE provider_nodes SET base_url=? WHERE name='mi-gemini'", (base_url,))
con.execute("UPDATE provider_connections SET provider_specific_data=? WHERE name='mi-gemini'", (json.dumps(psd),))
con.commit()
for r in con.execute("SELECT name, type, base_url FROM provider_nodes WHERE name='mi-gemini'"):
    print("Node:", r)
con.close()
print("✅ mi-gemini actualizado a la raíz")
