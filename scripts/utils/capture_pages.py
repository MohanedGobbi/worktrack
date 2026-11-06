import asyncio
from playwright.async_api import async_playwright
import os

worker_email = "john.doe@worktrack.com"
worker_pass = "Worker123!"

urls_to_capture = [
    {"name": "worker_portal", "url": "http://localhost:8000/worker-portal/"},
    {"name": "tasks", "url": "http://localhost:8000/tasks/"},
    {"name": "task_kanban", "url": "http://localhost:8000/tasks/kanban/"},
    {"name": "task_calendar", "url": "http://localhost:8000/tasks/calendar/"},
    {"name": "messaging", "url": "http://localhost:8000/messaging/"},
    {"name": "attendance", "url": "http://localhost:8000/attendance/"},
]

async def main():
    os.makedirs('pdf', exist_ok=True)
    print("Starting Playwright capture...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("Logging in...")
        await page.goto("http://localhost:8000/login/")
        
        await page.fill('input[name="email"]', worker_email)
        await page.fill('input[name="password"]', worker_pass)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')

        for item in urls_to_capture:
            print(f"Capturing {item['name']}...")
            await page.goto(item['url'])
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2) # Wait for animations
            
            # Save as PNG full image ("take ful image for each page")
            await page.screenshot(path=f"pdf/{item['name']}.png", full_page=True)
            # Save as PDF since folder was explicitly given as "pdf"
            await page.emulate_media(media="screen")
            await page.pdf(path=f"pdf/{item['name']}.pdf", format="A4", print_background=True, landscape=True)
            print(f"-> Saved pdf/{item['name']}.png and .pdf")
            
        await browser.close()
        print("Finished capturing all pages to the 'pdf' folder!")

if __name__ == "__main__":
    asyncio.run(main())
