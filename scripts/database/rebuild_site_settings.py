import re

with open('templates/pages/admin_dashboard.html', 'r') as f:
    admin_dash = f.read()

# Extract the CSS
css_match = re.search(r'<style>(.*?)</style>', admin_dash, re.DOTALL)
admin_css = css_match.group(1) if css_match else ""

# Pre-process the CSS to replace theme variables and hardcoded colors
replacements = [
    (r'var\(--color-primary\)', 'var(--preview-primary, #0ea5e9)'),
    (r'var\(--color-secondary\)', 'var(--preview-secondary, #64748b)'),
    (r'var\(--color-accent\)', 'var(--preview-accent, #10b981)'),
    (r'var\(--glass-bg-hex\)', 'var(--preview-glass-bg, #0f172a)'),
    (r'var\(--glass-border-hex\)', 'var(--preview-glass-border, #ffffff)'),
    (r'var\(--glow-color-hex\)', 'var(--preview-glow, #10b981)'),
    (r'var\(--glass-blur\)', 'var(--preview-glass-blur, 16px)'),
    (r'var\(--base-radius\)', 'var(--preview-radius, 16px)'),
    (r'var\(--widget-color-hex\)', 'var(--preview-widget-color, #1e293b)'),
    (r'#10b981', 'var(--preview-accent, #10b981)'),
    (r'#3b82f6', 'var(--preview-primary, #3b82f6)'),
    (r'#1e293b', 'var(--preview-widget-color, #1e293b)'),
]

for old, new in replacements:
    admin_css = re.sub(old, new, admin_css)

# Scope all CSS to #previewContainer
admin_css_scoped = "\n".join([f"#previewContainer {line}" if line.strip() and not line.strip().startswith('@') and not line.strip().startswith('/*') and not line.strip().startswith('}') and not line.strip().endswith('{') else line for line in admin_css.split('\n')])

with open('templates/pages/site_settings.html', 'r') as f:
    site_settings = f.read()

# We need to drop my custom .sim- layout inside #previewContainer and use the actual HTML structure
genuine_html = """
        <div class="preview-phone-wrap" id="previewContainer" style="flex-direction: row;">
            
            <style>
                #previewContainer {
                    --bg-page: var(--preview-bg-start, #020617);
                    font-family: var(--preview-font, 'Inter'), sans-serif;
                }
                #previewContainer .dashboard-main-area {
                    background: transparent !important;
                }
                #previewContainer .admin-hero {
                    background-image: linear-gradient(rgba(15,23,42,0.6), rgba(15,23,42,0.85)) !important;
                    background-size: cover !important;
                    background-position: center !important;
                }
                #previewContainer .neural-sidebar {
                    width: 220px;
                    height: 100%;
                    border-right: 1px solid color-mix(in srgb, var(--preview-glass-border, #ffffff) 20%, transparent);
                    background: color-mix(in srgb, var(--preview-glass-bg, #0f172a) 60%, transparent);
                    backdrop-filter: blur(var(--preview-glass-blur, 16px));
                }
                #previewContainer .ns-nav-link {
                    padding: 8px 16px; font-size: 0.8rem; margin-bottom: 2px;
                }
                #previewContainer .ns-nav-link.ns-active {
                    background: color-mix(in srgb, var(--preview-primary, #3b82f6) 20%, transparent);
                    color: var(--preview-primary, #3b82f6) !important;
                    border-left: 3px solid var(--preview-primary, #3b82f6);
                }
                #previewContainer .ns-nav-link.ns-active .ns-icon { color: var(--preview-primary, #3b82f6); }
                #previewContainer .ns-icon {
                    width: 20px; font-size: 0.9rem;
                }
                #previewContainer .ns-header {
                    padding: 16px; font-size: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05);
                }
                #previewContainer .ns-group-title {
                    padding: 16px 16px 8px; font-size: 0.6rem;
                }
                
                /* Paste scoped admin css */
                REPLACE_ME_CSS
                
                #previewContainer .admin-hero {
                    position: relative;
                    margin: 1rem;
                    border-radius: var(--preview-radius, 16px);
                    padding: 1.5rem;
                }
                #previewContainer .hero-metrics-row {
                    display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;
                }
                #previewContainer .metric-card-3, #previewContainer .metric-card-4 { display: none; } /* Show only 2 cards to fit */
                #previewContainer .circles-container { transform: scale(0.7); transform-origin: top right; }
                
                #previewBgObj, #previewBannerObj {
                    position: absolute; top:0; left:0; width:100%; height:100%; object-fit: cover; opacity: 0.4; pointer-events: none; z-index: 0;
                }
                #previewBannerObj {
                    mix-blend-mode: overlay; opacity: 0.3; pointer-events: none;
                }
            </style>
            
            <!-- Global Background -->
            <img src="{% if site_config.background_image %}{{ site_config.background_image.url }}{% endif %}" id="previewBgObj" style="{% if not site_config.background_image %}display: none;{% endif %}; z-index: -1;">
            
            <!-- Sidebar -->
            <aside class="neural-sidebar flex-shrink-0">
                <div class="ns-header">
                    <img src="{% if site_config.logo %}{{ site_config.logo.url }}{% else %}/media/logo.png{% endif %}" alt="Logo" width="24" height="24" class="bg-white rounded p-1" id="previewLogoImg">
                    <div id="previewBrandText" class="ms-2 fw-bold text-truncate">{{ site_config.app_name|default:"Secretariat" }}</div>
                </div>
                <div class="ns-group-title">Command Hub</div>
                <div class="ns-nav-link"><div class="ns-icon"><i class="fas fa-home"></i></div> Home</div>
                <div class="ns-nav-link ns-active"><div class="ns-icon"><i class="fas fa-tachometer-alt"></i></div> Dashboard</div>
                
                <div class="ns-group-title">Operations</div>
                <div class="ns-nav-link"><div class="ns-icon"><i class="fas fa-tasks"></i></div> Active Tasks</div>
                <div class="ns-nav-link"><div class="ns-icon"><i class="fas fa-columns"></i></div> Kanban Board</div>
            </aside>
            
            <!-- Main Content Area -->
            <div class="flex-grow-1 dashboard-main-area" style="position: relative; overflow-y: auto;">
                
                <!-- Hero Banner -->
                <div class="admin-hero" id="simBanner">
                    <img src="{% if site_config.banner_image %}{{ site_config.banner_image.url }}{% endif %}" id="previewBannerObj" style="{% if not site_config.banner_image %}display: none;{% endif %}; mix-blend-mode: overlay; z-index: 1;">
                    <div class="streak-1" style="z-index: 2;"></div>
                    <div class="streak-2" style="z-index: 2;"></div>
                    <div class="hero-content" style="z-index: 3; position: relative;">
                        <div class="row w-100 m-0">
                            <div class="col-6">
                                <div class="live-pill"><i class="fas fa-satellite-dish"></i> LIVE CONTROL</div>
                                <h1 class="hero-title pt-2" style="font-size: 1.5rem; line-height: 1.2;">System <br><span style="color: var(--preview-accent, #10b981);">Command Center</span></h1>
                                <div class="tick-list mt-3">
                                    <div style="font-size: 0.7rem;"><i class="fas fa-check-square"></i> Real-time Sync</div>
                                    <div style="font-size: 0.7rem;"><i class="fas fa-check-square"></i> Smart Analytics</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="circles-container d-flex justify-content-end gap-3">
                                    <div class="glow-circle" style="width: 80px; height: 80px; --pc: 100%; border: 4px solid var(--preview-accent, #10b981); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem; color: white;">85%</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Mini Metrics Row -->
                        <div class="hero-metrics-row mt-4 px-2 container-fluid">
                            <div class="hero-metric-card">
                                <div class="metric-header"><div class="metric-icon" style="color: var(--preview-accent, #10b981);"><i class="fas fa-users"></i></div><h3 class="metric-title">STAFF FORCE</h3></div>
                                <div class="metric-val">142</div>
                                <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 100%; background: var(--preview-accent, #10b981);"></div></div>
                            </div>
                            <div class="hero-metric-card">
                                <div class="metric-header"><div class="metric-icon" style="color: var(--preview-primary, #3b82f6);"><i class="fas fa-bolt"></i></div><h3 class="metric-title">EFFICIENCY</h3></div>
                                <div class="metric-val">94%</div>
                                <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: 94%; background: var(--preview-primary, #3b82f6);"></div></div>
                            </div>
                        </div>
                    </div>
                </div>
                
            </div>
            
        </div>
"""

genuine_html = genuine_html.replace('REPLACE_ME_CSS', admin_css_scoped)

# replace inside site_settings
new_site_settings = re.sub(
    r'<div class="preview-phone-wrap" id="previewContainer">.*?</div>\s*</div>\s*<!-- RIGHT: Settings Editor Panel -->',
    genuine_html + '\n    </div>\n\n    <!-- RIGHT: Settings Editor Panel -->',
    site_settings,
    flags=re.DOTALL
)

with open('templates/pages/site_settings.html', 'w') as f:
    f.write(new_site_settings)
