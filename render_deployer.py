# -----------------------------------------------------------------------------
# Project: GagaraGogo Setup Bot
# Component: render_deployer.py
# Author: chaolcam (https://github.com/chaolcam/gagaragogo-userbot)
# License: GNU GPL v3.0
# Copyright (c) 2026 chaolcam
# -----------------------------------------------------------------------------
import aiohttp

GGR_RENDER_API_BASE = "https://api.render.com/v1"
GGR_REPO_URL = "https://github.com/chaolcam/gagaragogo-userbot"
GGR_BRANCH = "main"

class GgrRenderDeployer:
    """Render.com REST API üzerinden GagaraGogo servisini oluşturan ve yöneten sınıf."""

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def get_owner_id(self) -> str:
        """Render API anahtarını doğrular ve kullanıcının workspace/owner ID'sini çeker."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{GGR_RENDER_API_BASE}/owners") as resp:
                if resp.status != 200:
                    raise Exception("Render API anahtarı geçersiz veya yetkisiz! Lütfen anahtarınızı kontrol edin.")
                data = await resp.json()
                if not data or not isinstance(data, list):
                    raise Exception("Render hesabınızda uygun bir Workspace/Owner bulunamadı.")
                owner = data[0].get("owner") or data[0]
                return owner.get("id")

    async def deploy_service(self, env_vars: dict) -> dict:
        """
        Render hesabında gagaragogo-userbot web servisini oluşturur ve değişkenleri ekler.
        """
        owner_id = await self.get_owner_id()

        env_vars_list = [
            {"key": k, "value": str(v)} for k, v in env_vars.items()
        ]

        payload = {
            "type": "web_service",
            "name": "gagaragogo-userbot",
            "ownerId": owner_id,
            "repo": GGR_REPO_URL,
            "branch": GGR_BRANCH,
            "autoDeploy": "yes",
            "envVars": env_vars_list,
            "serviceDetails": {
                "plan": "free",
                "region": "frankfurt",
                "env": "python",
                "envSpecificDetails": {
                    "buildCommand": "pip install -U -r requirements.txt",
                    "startCommand": "python3 main.py"
                }
            }
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{GGR_RENDER_API_BASE}/services", json=payload) as resp:
                data = await resp.json()
                if resp.status not in (200, 201):
                    msg = data.get("message") or str(data)
                    raise Exception(f"Render servisi oluşturulamadı: {msg}")
                
                service = data.get("service") or data
                service_id = service.get("id")

                # Değişkenleri PUT endpointi ile de kesinleştir
                try:
                    await session.put(f"{GGR_RENDER_API_BASE}/services/{service_id}/env-vars", json=env_vars_list)
                    await session.post(f"{GGR_RENDER_API_BASE}/services/{service_id}/deploys", json={"clearCache": "do_not_clear"})
                except Exception:
                    pass
                
                # Render'ın bu servise atadığı benzersiz alt alan adını (unique onrender.com URL'i) al
                unique_url = service.get("serviceDetails", {}).get("url")
                if not unique_url and service.get("slug"):
                    unique_url = f"https://{service.get('slug')}.onrender.com"

                # Render bazen URL'i 2-3 saniye sonra atar; kesinleştirmek için servisi tekrar sorgula
                if not unique_url or "onrender.com" not in str(unique_url):
                    import asyncio
                    await asyncio.sleep(2.5)
                    async with session.get(f"{GGR_RENDER_API_BASE}/services/{service_id}") as detail_resp:
                        if detail_resp.status == 200:
                            det_data = await detail_resp.json()
                            det_srv = det_data.get("service") or det_data
                            unique_url = det_srv.get("serviceDetails", {}).get("url")
                            if not unique_url and det_srv.get("slug"):
                                unique_url = f"https://{det_srv.get('slug')}.onrender.com"

                dashboard_url = f"https://dashboard.render.com/web/{service_id}"
                if not unique_url:
                    unique_url = dashboard_url

                return {
                    "status": "success",
                    "id": service_id,
                    "name": service.get("name"),
                    "service_url": unique_url,
                    "dashboard_url": dashboard_url
                }

    async def delete_userbot_service(self) -> bool:
        """
        Render hesabında 'gagaragogo-userbot' adındaki servisi bulur ve tamamen siler.
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{GGR_RENDER_API_BASE}/services?limit=50") as resp:
                if resp.status != 200:
                    raise Exception("Render servisleri listelenemedi. API anahtarınızı kontrol edin.")
                services = await resp.json()

            bulundu = False
            for item in services:
                srv = item.get("service") or item
                if "gagaragogo-userbot" in srv.get("name", "").lower():
                    srv_id = srv.get("id")
                    async with session.delete(f"{GGR_RENDER_API_BASE}/services/{srv_id}") as del_resp:
                        if del_resp.status in (200, 204):
                            bulundu = True
            return bulundu

# Uyumluluk aliası
RenderDeployer = GgrRenderDeployer
