import sqlite3, json
psd = {"prefix": "mi-gemini", "apiType": "chat", "baseUrl": "https://generativelanguage.googleapis.com/v1beta", "nodeName": "mi-gemini"}
con = sqlite3.connect("data/storage.sqlite")
con.execute("UPDATE provider_nodes SET type='gemini', base_url='https://generativelanguage.googleapis.com/v1beta' WHERE name='mi-gemini'")
con.execute("UPDATE provider_connections SET provider_specific_data=? WHERE name='mi-gemini'", (json.dumps(psd),))
con.commit()
for r in con.execute("SELECT name, type, base_url FROM provider_nodes WHERE name='mi-gemini'"):
    print("Node:", r)
con.close()
print("✅ mi-gemini actualizado a nativo")
