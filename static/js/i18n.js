(function () {
    const LANG_KEY = 'worktrack_lang';

    function setLanguageCookie(lang) {
        document.cookie = `django_language=${encodeURIComponent(lang)}; path=/; max-age=${60 * 60 * 24 * 365}`;
        document.cookie = `worktrack_lang=${encodeURIComponent(lang)}; path=/; max-age=${60 * 60 * 24 * 365}`;
    }

    function buildReverseTranslations() {
        if (!translations.en) translations.en = {};
        if (translations.ar) {
            for (const [enKey, arVal] of Object.entries(translations.ar)) {
                if (arVal && typeof arVal === 'string' && arVal.trim().length > 0) {
                    const cleanEn = enKey.trim();
                    const cleanAr = arVal.trim();
                    if (cleanAr && cleanEn) {
                        translations.en[cleanAr] = cleanEn;
                        const normAr = cleanAr.replace(/\s+/g, ' ');
                        translations.en[normAr] = cleanEn;
                    }
                }
            }
        }
    }

    function mergeDbTranslations(data) {
        if (!data || typeof data !== 'object') return;
        if (data.ar && typeof data.ar === 'object') {
            translations.ar = Object.assign({}, translations.ar, data.ar);
        }
        if (data.en && typeof data.en === 'object') {
            translations.en = Object.assign({}, translations.en, data.en);
        }
        buildReverseTranslations();
    }

    function loadDbTranslations() {
        // The DB map endpoint is not routed (it would ship ~3k machine-generated rows to every page).
        // Admin translations reach pages through the server-side DynamicTranslationMiddleware instead.
        if (!window.__wtClientTranslationMap) return;
        fetch('/translations/api/map/?_t=' + Date.now(), { credentials: 'same-origin', cache: 'no-store' })
            .then(response => {
                if (!response.ok) throw new Error('No DB translation map');
                return response.json();
            })
            .then(data => {
                mergeDbTranslations(data);
                if (typeof translateAll === 'function') {
                    translateAll();
                }
            })
            .catch(() => {
                // Ignore failures and continue with built-in translations
            });
    }

    Object.defineProperty(window, '__isArabic', {
        get: function () {
            return localStorage.getItem(LANG_KEY) === 'ar';
        },
        configurable: true
    });

    const translations = {
        "ar": {
            "": "\\",
            "Type your message...": "اكتب رسالتك هنا...",
            "Type a message...": "اكتب رسالة...",
            "Search conversations or users...": "بحث في المحادثات أو المستخدمين...",
            "Search in chat...": "البحث في المحادثة...",
            "Search members by name...": "بحث عن الأعضاء بالاسم...",
            "Send Message": "إرسال الرسالة",
            "Attach File": "إرفاق ملف",
            "Create Poll": "إنشاء استطلاع",
            "Voice Note": "تسجيل صوتي",
            "Send Voice Note": "إرسال التسجيل الصوتي",
            "Discard Voice Note": "إلغاء التسجيل الصوتي",
            "Cancel Reply": "إلغاء الرد",
            "Remove File": "إزالة الملف",
            "Discard": "إلغاء",
            "Emoji": "رمز تعبيري",
            "e.g. What's for lunch?": "مثال: ما هو رأيك؟",
            "e.g. Development Team": "مثال: فريق العمل",
            "Option 1": "الخيار 1",
            "Option 2": "الخيار 2",
            " button on specific module cards.": "يمكن إضافة الملاحظات عبر زر \\",
            "&lt;5ms": "أقل من 5 مللي ثانية",
            "( hrs)": "( ساعة)",
            "(Completed Tasks / Total Assignments) × 100": "(المهام المكتملة / إجمالي التعيينات) × 100",
            "(Correspondence PDF)": "(ملف PDF للمراسلة)",
            "(for widget display)": "(لعرض الأداة)",
            "* Required": "* مطلوب",
            "-- Choose Category --": "-- اختر الفئة --",
            "-- Choose an assigned task --": "-- اختر مهمة معينة --",
            "-- Select Module --": "-- اختر الوحدة --",
            "-- Select Priority --": "-- اختر الأولوية --",
            "-- Select Status --": "-- اختر الحالة --",
            "-- Select Type --": "-- اختر النوع --",
            "-- Select Wilaya --": "-- اختر الولاية --",
            "e.g., Serial Number": "مثال: الرقم التسلسلي",
            "Option 1, Option 2, Option 3": "الخيار 1، الخيار 2، الخيار 3",
            "/ Module Templates": "/ قوالب النماذج",
            "0 files selected": "0 ملفات محددة",
            "0% (Started)": "0% (بدأت)",
            "0.02s": "0.02 ثانية",
            "04 / DEPLOYMENT": "04 / النشر والتثبيت",
            "1.2M": "1.2 مليون",
            "10 NODES": "10 عقد",
            "100 NODES": "100 عقدة",
            "100% (Finished)": "100% (منتهٍ)",
            "10M": "10 مليون",
            "12 IN WORKLIST": "12 في قائمة العمل",
            "120k": "120 ألف",
            "18k+": "أكثر من 18 ألف",
            "1st Place": "المرتبة الأولى",
            "1st Place champion in Algerian national digital themes and thesis presentation competitions.": "بطل المركز الأول في المسابقات الوطنية الجزائرية للمواضيع الرقمية وعرض الأطروحات.",
            "2 Modules": "2 وحدات",
            "2 yrs": "سنتان",
            "2.4k": "2.4 ألف",
            "2.5k+": "أكثر من 2.5 ألف",
            "3 Levels": "3 مستويات",
            "4.2M": "4.2 مليون",
            "50 NODES": "50 عقدة",
            "50% (Halfway)": "50% (منتصف الطريق)",
            "5k m": "5 آلاف متر",
            "80% COMPLETE": "80% مكتمل",
            "> --- CORE SYSTEM PORTFOLIO ACTIVE ---": "> --- محفظة الأنظمة الأساسية نشطة ---",
            "> --- NATIONAL HONORS & DISTINCTIONS ---": "> --- الأوسمة والتميز الوطني ---",
            "> --- PEER-REVIEWED SCIENTIFIC LITERATURE ---": "> --- المنشورات العلمية المحكمة ---",
            "> --- RESEARCH & SYSTEM ARCHITECTURE TELEMETRY ---": "> --- قياسات بنية الأنظمة والأبحاث ---",
            "> ACCESS IDENT: DR. DEGHA HOUSSEM EDDINE (ASSOCIATE PROFESSOR, CATEGORY A)": "> هوية الدخول: د. دغة حسام الدين (أستاذ محاضر، قسم أ)",
            "> DHE_CORE // INITIALIZING SECURE ACADEMIC & RESEARCH ENCLAVE...": "> DHE_CORE // تهيئة الجيب الأكاديمي والبحثي الآمن...",
            "> DHE_CORE // INTEGRITY CHECK: 100% SECURE": "> DHE_CORE // فحص السلامة: آمن 100%",
            "> INSTITUTION: KASDI MERBAH UNIVERSITY, OUARGLA": "> المؤسسة: جامعة قاصدي مرباح، ورقلة",
            "> ORCID ID: 4473-3401-0002-0000 // STATUS: VERIFIED": "> معرف ORCID: 4473-3401-0002-0000 // الحالة: تم التحقق",
            "> STATUS: DR. DEGHA HOUSSEM EDDINE ACADEMIC RESEARCH ENGINE ONLINE & ACTIVE": "> الحالة: محرك الأبحاث الأكاديمية للدكتور دغة حسام الدين متصل ونشط",
            "> [AWARD FIELD] Digital Themes & Advanced Technological Innovations": "> [مجال الجائزة] المواضيع الرقمية والابتكارات التكنولوجية المتقدمة",
            "> [AWARD] 1st Place - Algerian National 'My Thesis in 180 Seconds' (MT180) 2021": "> [جائزة] المركز الأول - المسابقة الوطنية الجزائرية 'أطروحتي في 180 ثانية' (MT180) 2021",
            "> [CONF] Smart Building Simulator - Ambient Assisted Living & Multi-Agent Systems": "> [مؤتمر] Smart Building Simulator - العيش المدعوم بالمحيط وأنظمة متعددة الوكلاء",
            "> [PORT] HTTP server listening on port 8000 (SECURE)": "> [منفذ] خادم HTTP يستمع على المنفذ 8000 (آمن)",
            "> [PUB] Frontiers in Microbiology - Causal Machine Learning for Microbiome Analysis": "> [منشور] Frontiers in Microbiology - التعلم الآلي السببي لتحليل الميكروبيوم",
            "> [PUB] IJERPH - Empirical Study on ICT and Infant Mortality in Low-Income Countries": "> [منشور] IJERPH - دراسة تجريبية حول تكنولوجيا المعلومات والاتصالات ووفيات الرضع في البلدان منخفضة الدخل",
            "> [SYSTEM] AgriPest: Scientific Library, Computer Vision & Sightings Platform": "> [نظام] AgriPest: المكتبة العلمية، الرؤية الحاسوبية ومنصة الرصد",
            "> [SYSTEM] IDRAK: Enterprise SaaS for Administrative Workflow Orchestration": "> [نظام] إدراك: برمجيات كخدمة للمؤسسات لتنسيق سير العمل الإداري",
            "> [SYSTEM] Open-SBS: Causal Thermodynamic Digital Twin & Multi-Agent Simulator": "> [نظام] Open-SBS: التوأم الحراري الرقمي السببي ومحاكي متعدد الوكلاء",
            "> [SYSTEM] Voltix: AI Smart Grid High-Throughput Substation Telemetry": "> [نظام] Voltix: القياس عن بعد للمحطات الفرعية عالية الإنتاجية للشبكة الذكية بالذكاء الاصطناعي",
            "> [SYSTEM] WorkTrack Pro™: General Secretariat Operations & Task Tracking Hub": "> [نظام] WorkTrack Pro™: عمليات الأمانة العامة ومركز تتبع المهام",
            "> [TECH] PyTorch, TensorFlow, CausalML, DoubleML, Django, FastAPI, Linux kernel": "> [تقنيات] PyTorch, TensorFlow, CausalML, DoubleML, Django, FastAPI, نواة Linux",
            "A brief overview of this template": "نبذة مختصرة عن هذا القالب",
            "A complex computer vision ecosystem mapping agricultural infestation vectors. Leverages PyMuPDF in the backend for article classification, generating document first-page screenshots as covers, and integrates a dynamic Leaflet geographical mapping engine for active sightings tracking.": "نظام بيئي معقد للرؤية الحاسوبية يرسم خرائط لنواقل الآفات الزراعية. يستفيد من PyMuPDF في الخلفية لتصنيف المقالات، وتوليد لقطات شاشة للصفحة الأولى للمستندات كأغلفة، ويدمج محرك رسم خرائط جغرافية Leaflet لتتبع المشاهدات النشطة.",
            "A distraction-free zone focused purely on execution. Clear priorities, obvious deadlines, and a seamless submission process.": "منطقة خالية من التشتيت تركز بالكامل على التنفيذ. أولويات واضحة، مواعيد نهائية واضحة، وعملية تقديم سلسة.",
            "A high-fidelity building simulator modeling thermal interactions, multi-agent occupancy behaviors, and causal policy estimators for energy conservation.": "محاكاة مبانٍ عالية الدقة لنمذجة التفاعلات الحرارية، وسلوكيات الإشغال متعددة الوكلاء، ومقرار ت السياسات السببية للحفاظ على الطاقة.",
            "A new version has been requested.": "تم طلب إصدار جديد.",
            "A seamless partnership from start to finish. The administrative IDRAK hub was delivered with zero friction and outstanding UI elegance.": "شراكة سلسة من البداية إلى النهاية. تم تسليم مركز إدراك الإداري بدون أي احتكاك وأناقة واجهة مستخدم متميزة.",
            "A state-of-the-art simulation system leveraging causal machine learning and multi-agent thermodynamic interactions to predict building energy consumption and optimize resource scheduling.": "نظام محاكاة متطور يستفيد من التعلم الآلي السببي وتفاعلات الديناميكا الحرارية متعددة الوكلاء للتنبؤ باستهلاك الطاقة في المباني وتحسين جدولة الموارد.",
            "A structured, undeniable chain of custody for every task.": "سلسلة عهدة منظمة وموثقة لكل مهمة.",
            "A true technical partner. The depth of medical systems architecture and engineering knowledge he brings is unmatched. Highly recommended for complex digital transformation.": "شريك تقني حقيقي. إن عمق المعرفة بهندسة الأنظمة الطبية التي يقدمها لا مثيل له. يوصى به بشدة للتحول الرقمي المعقد.",
            "ACADEMIC & RESEARCH IMPACT": "الأثر الأكاديمي والبحثي",
            "ACTIVE": "نشط",
            "ACTIVE PAGE": "الصفحة النشطة",
            "ACTIVE PROFILE": "الملف الشخصي نشط",
            "ACTIVE TASKS": "المهام النشطة",
            "AI Curriculum": "منهج الذكاء الاصطناعي",
            "AI Dashboards": "لوحات تحكم بالذكاء الاصطناعي",
            "ALL MODES": "جميع الأوضاع",
            "ALL RANKS": "جميع الرتب",
            "API Reference": "واجهة برمجة التطبيقات",
            "APR": "أبريل",
            "ARCHIVED / DONE": "مؤرشف / مكتمل",
            "ASAP": "في أسرع وقت",
            "ATTACHMENTS (MULTI)": "مرفقات (متعددة)",
            "ATTENDANCE CONFIGURATION": "إعدادات الحضور",
            "AUG": "أغسطس",
            "AWS": "إيه دبليو إس",
            "About Me": "من أنا",
            "Absent": "غائب",
            "Absent Today": "غائب اليوم",
            "Absent:": "غائب:",
            "Academic Authority": "السلطة الأكاديمية",
            "Access Control": "التحكم في الوصول",
            "Access IP": "عنوان IP",
            "Access Laboratory": "دخول المختبر",
            "Access Portal": "بوابة الدخول",
            "Accomplishments": "الإنجازات",
            "Account Status": "حالة الحساب",
            "Accuracy": "الدقة",
            "Ack": "إقرار",
            "Acknowledge Receipt": "الإقرار بالاستلام",
            "Acknowledgement": "إقرار",
            "Action": "الإجراء",
            "Action Item / Module": "عنصر العمل / الوحدة",
            "Action Required": "إجراء مطلوب",
            "Actions": "إجراءات",
            "Activate Map": "تنشيط الخريطة",
            "Active": "نشط",
            "Active Board": "لوحة نشطة",
            "Active Case Studies": "الدراسات النشطة",
            "Active Depts": "الأقسام النشطة",
            "Active Modules": "وحدات نشطة",
            "Active Nodes": "العقد النشطة",
            "Active Personnel": "الأفراد النشطون",
            "Active Projects": "مشاريع نشطة",
            "Active Tasks": "المهام النشطة",
            "Active Team Members": "أعضاء الفريق النشطين",
            "Active across all modules": "نشط عبر جميع الوحدات",
            "Active user profile": "ملف المستخدم النشط",
            "Activity Log": "سجل النشاط",
            "Add Custom Field": "إضافة حقل مخصص",
            "Add Field": "إضافة حقل",
            "Add Module": "إضافة وحدة",
            "Add More Files": "إضافة المزيد من الملفات",
            "Add Strategic Note": "إضافة ملاحظة استراتيجية",
            "Add Workflow Unit": "إضافة وحدة سير العمل",
            "Add a reminder or task for the team.": "إضافة تذكير أو مهمة للفريق.",
            "Add any notes or comments about your submission...": "أضف أي ملاحظات أو تعليقات حول تقديمك...",
            "Add clear notes explaining your work": "أضف ملاحظات واضحة تشرح عملك",
            "Add details or notes...": "إضافة تفاصيل أو ملاحظات...",
            "Add new action item...": "إضافة عنصر عمل جديد...",
            "Additional Task Files (Discussion/Reference)": "ملفات مهام إضافية (مناقشة/مرجع)",
            "Additional context (optional)...": "سياق إضافي (اختياري)...",
            "Address": "عنوان",
            "Admin": "مسؤول",
            "Admin Center": "مركز الإدارة",
            "Admin Dashboard": "لوحة تحكم الإدارة",
            "Admin Delete": "حذف مسؤول",
            "Admin Hub": "مركز الإدارة",
            "Admin Portal": "بوابة الإدارة",
            "Administration": "الإدارة",
            "Administrative Category": "الفئة الإدارية",
            "Administrative Correspondence": "المراسلات الإدارية",
            "Administrative Correspondence — Worktrack Pro": "المراسلات الإدارية — وورك تراك برو",
            "Admins": "المدراء",
            "Advanced AI Solutions": "حلول الذكاء الاصطناعي المتقدمة",
            "Advanced econometrics and causal machine learning estimators to evaluate health policy and predict outcomes.": "الاقتصاد القياسي المتقدم ومقدرات التعلم الآلي السببي لتقييم السياسات الصحية والتنبؤ بالنتائج.",
            "Afghanistan": "أفغانستان",
            "Agent Simulation": "محاكاة الوكيل",
            "Agents": "الوكلاء",
            "AgriPest Intelligence & Scientific Library": "أجريبست الذكي والمكتبة العلمية",
            "AgriPest Intelligence Portal": "بوابة أجريبست الذكية",
            "Agricultural Officer": "مسؤول زراعي",
            "Albania": "ألبانيا",
            "Algeria": "الجزائر",
            "All": "الكل",
            "All Groups": "جميع المجموعات",
            "All Caught Up!": "كل شيء محدث!",
            "All Clear!": "كل شيء واضح!",
            "All Records": "جميع السجلات",
            "All Status": "جميع الحالات",
            "All Submissions": "جميع التقديمات",
            "All Tasks": "جميع المهام",
            "All Types": "جميع الأنواع",
            "All caught up!": "كل شيء محدث!",
            "Alpha": "ألفا",
            "An administrative workflow platform syncing general secretariat task tracking, official correspondence, attendance sheets, and real-time Gantt schedule charts.": "منصة سير عمل إدارية توائم تتبع مهام الأمانة العامة، والمراسلات الرسمية، وأوراق الحضور، ومخططات غانت الزمنية المباشرة.",
            "An automated research catalog and computer vision sighting system featuring document parsing, screenshot extraction, and interactive geo-sightings maps.": "كتالوج أبحاث مؤتمت ونظام رصد للرؤية الحاسوبية يتميز بتحليل المستندات واستخراج لقطات الشاشة وخرائط رصد جغرافية تفاعلية.",
            "An enterprise-grade administrative orchestration platform designed for general secretariat task tracking, official correspondence workflow mapping, and live interactive Gantt scheduler views.": "منصة تنسيق إداري للمؤسسات مصممة لتتبع مهام الأمانة العامة، ورسم خرائط سير العمل للمراسلات الرسمية، وعرض مخططات غانت التفاعلية المباشرة.",
            "Analysis Node": "عقدة التحليل",
            "Analytics": "التحليلات",
            "Andorra": "أندورا",
            "Angola": "أنغولا",
            "Antigua and Barbuda": "أنتيغوا وبربودا",
            "App Name & Colors": "اسم التطبيق والألوان",
            "Append to Workflow": "إلحاق بسير العمل",
            "Approve Selected": "موافقة على المحدد",
            "Approve Submission": "الموافقة على التقديم",
            "Approved": "موافق عليه",
            "Approved Changes Requested Submittal Comment": "موافق عليه، طلب تغيير، تقديم، تعليق",
            "Archive": "أرشفة",
            "Archived": "مؤرشف",
            "Archived Units": "وحدات مؤرشفة",
            "Arduino": "أردوينو",
            "Are you sure you want to delete this submission? This action cannot be undone.": "هل أنت متأكد من حذف هذا التقديم؟ لا يمكن التراجع عن هذا الإجراء.",
            "Are you sure you want to proceed?": "هل أنت متأكد من رغبتك بالاستمرار؟",
            "Are you sure?": "هل أنت متأكد؟",
            "Argentina": "الأرجنتين",
            "Armenia": "أرمينيا",
            "Assign Task": "تعيين مهمة",
            "Assign To": "تعيين إلى",
            "Assign an evaluation score for this work quality.": "تعيين درجة تقييم لجودة هذا العمل.",
            "Assign to Users": "التعيين للمستخدمين",
            "Assigned To": "مسند إلى",
            "Assignee": "المكلف",
            "Assignment": "التعيين والتكليف",
            "Associate Professor & Data Scientist": "أستاذ محاضر وعالم بيانات",
            "Associate Professor & Software Developer": "أستاذ محاضر ومطور برمجيات",
            "Associate Professor, Category A": "أستاذ محاضر، قسم أ",
            "Associated Task": "المهمة المرتبطة",
            "Attach Guidance File (Optional)": "إرفاق ملف توجيهي (اختياري)",
            "Attach Specifications / File (Optional)": "إرفاق المواصفات / ملف (اختياري)",
            "Attached Files": "الملفات المرفقة",
            "Attachments & Covers": "المرفقات والأغلفة",
            "Attendance": "الحضور",
            "Attendance Policy Settings": "إعدادات سياسة الحضور",
            "Attendance Tracking": "تتبع الحضور",
            "Attendance Tracking (NEW)": "تتبع الحضور (جديد)",
            "Attendance Tracking - Worktrack Pro": "تتبع الحضور - وورك تراك برو",
            "Attention: Resubmission Required": "انتباه: إعادة الإرسال مطلوبة",
            "Australia": "أستراليا",
            "Austria": "النمسا",
            "Automated CI/CD deployment pipelines, containerized microservices orchestration, and infrastructure as code.": "خطوط نشر CI/CD المؤتمتة، وتنسيق الخدمات المصغرة المعبأة في حاويات، والبنية التحتية ككود.",
            "Automated Reactivation": "تفعيل تلقائي",
            "Automatically cache map tiles for all": "تخزين بلاطات الخريطة مؤقتاً تلقائياً للكل",
            "Automatically reset task progress and move deadline forward.": "إعادة تعيين تقدم المهمة تلقائياً ونقل الموعد النهائي للأمام.",
            "Autonomous Fleet Coordinator": "منسق الأسطول الذاتي",
            "Available:": "متاح:",
            "Available: 4": "متاح: 4",
            "Avg": "متوسط",
            "Avg Completion": "متوسط الإنجاز",
            "Avg Quality": "متوسط الجودة",
            "Avg Team Completion": "متوسط إنجاز الفريق",
            "Avg. Module Progress": "متوسط تقدم الوحدة",
            "Awaiting Acknowledgement": "في انتظار الإقرار",
            "Awaiting Productivity Data": "في انتظار بيانات الإنتاجية",
            "Awaiting Review": "في انتظار المراجعة",
            "Azerbaijan": "أذربيجان",
            "BUSINESS & SOFTWARE ENGINEERING METRICS": "مؤشرات الأعمال وهندسة البرمجيات",
            "Back": "رجوع",
            "Back to": "العودة إلى",
            "Back to Correspondence": "العودة للمراسلات",
            "Back to Dashboard": "العودة للوحة القيادة",
            "Back to Task": "العودة إلى المهمة",
            "Back to Templates": "العودة للقوالب",
            "Bahamas": "جزر البهاما",
            "Bahrain": "البحرين",
            "Bangladesh": "بنغلاديش",
            "Barbados": "باربادوس",
            "Base Command": "القيادة الأساسية",
            "Basic Information": "معلومات أساسية",
            "Batch Sync & Caching": "مزامنة مجمعة وتخزين مؤقت",
            "Batch Task Sync": "مزامنة المهام الجماعية",
            "Battery": "البطارية",
            "Belarus": "بيلاروسيا",
            "Belgium": "بلجيكا",
            "Belize": "بليز",
            "Benin": "بنين",
            "Bhutan": "بوتان",
            "Biography & Academic Profile": "السيرة الذاتية والملف الأكاديمي",
            "Bioinformatics Researcher": "باحث في المعلوماتية الحيوية",
            "Bolivia": "بوليفيا",
            "Bootcamps": "دورات مكثفة",
            "Bosnia and Herzegovina": "البوسنة والهرسك",
            "Both Layers (Street & Satellite)": "كلا الطبقتين (شوارع وأقمار صناعية)",
            "Botswana": "بوتسوانا",
            "Brazil": "البرازيل",
            "Browse": "تصفح",
            "Brunei": "بروناي",
            "Build Process": "عملية البناء",
            "Builder": "منشئ",
            "Built to meet the strict compliance requirements of the General Secretariat.": "مصمم لتلبية متطلبات الامتثال الصارمة للأمانة العامة.",
            "Bulgaria": "بلغاريا",
            "Bulk Delete": "حذف جماعي",
            "Burkina Faso": "بوركينا فاسو",
            "Burundi": "بوروندي",
            "C++": "سي++",
            "C++ & MQTT": "C++ و MQTT",
            "CLEARANCE: SYSTEM OPERATOR": "التصريح: مشغل النظام",
            "COMMAND CENTER": "مركز القيادة",
            "COMPLETED": "مكتمل",
            "COMPLETION": "الانتهاء",
            "COMPLETION RATE": "معدل الإنجاز",
            "CORE IDENTITY": "الهوية الأساسية",
            "CORE PAGE:": "الصفحة الأساسية:",
            "CORE PAGE:  OF": "الصفحة الأساسية:  من",
            "CORRESPONDENCE": "المراسلات",
            "CURRENT PHASE": "المرحلة الحالية",
            "Cache Info": "معلومات التخزين المؤقت",
            "Cached Tiles": "البلاطات المخزنة مؤقتاً",
            "Calculated monthly scores will be showcased here.": "ستُعرض الدرجات الشهرية المحسوبة هنا.",
            "Calendar": "التقويم",
            "Calendar View": "عرض التقويم",
            "Cambodia": "كمبوديا",
            "Cameroon": "الكاميرون",
            "Canada": "كندا",
            "Cancel": "إلغاء",
            "Cape Verde": "الرأس الأخضر",
            "Case Studies": "دراسات الحالة",
            "Causal ML Consultancy": "استشارات التعلم الآلي السببي",
            "Causal ML Integration": "تكامل التعلم الآلي السببي",
            "Central African Republic": "جمهورية أفريقيا الوسطى",
            "Certified": "المعتمدة",
            "Chad": "تشاد",
            "Change Module Context": "تغيير سياق الوحدة",
            "Changes to the Office Start Time immediately affect the next person who clocks in, but do not alter historical records.": "تؤثر التغييرات في وقت بدء العمل في المكتب فوراً على الشخص التالي الذي يسجل دخوله، ولكنها لا تغير السجلات التاريخية.",
            "Chat permissions": "أذونات الدردشة",
            "Check In": "تسجيل الدخول",
            "Check In Now": "تسجيل الدخول الآن",
            "Check Out": "تسجيل الخروج",
            "Chile": "شيلي",
            "China": "الصين",
            "Chloe M.": "كلوي م.",
            "Chronic Late Arrivals (This Month)": "حالات التأخر المزمنة (هذا الشهر)",
            "Circular": "منشور رسمي",
            "Circulars": "التعاميم",
            "Circulars, directives, memos — requires acknowledgement": "المنشورات، التوجيهات، المذكرات — تتطلب إقراراً بالاستلام",
            "Clear": "مسح",
            "Clear All": "مسح الكل",
            "Clear All Cache": "مسح كل التخزين المؤقت",
            "Clear Cache": "مسح التخزين المؤقت",
            "Clear Selection": "مسح التحديد",
            "Clear answers to frequent inquiries regarding project scope, pricing, and infrastructure.": "أجوبة واضحة للاستفسارات المتكررة بخصوص نطاق المشروع والتسعير والبنية التحتية.",
            "Client Testimonials": "آراء العملاء",
            "Clock In": "تسجيل الحضور",
            "Clock Out": "تسجيل الانصراف",
            "Close": "إغلاق",
            "Cloud Infrastructure & DevOps": "البنية التحتية السحابية وDevOps",
            "Collaboration on training curriculum and bootcamp structures was outstanding. Dr. Degha combines academic pedagogy with pure engineering excellence.": "كان التعاون في مناهج التدريب وهياكل المعسكرات التدريبية متميزاً. يجمع د. دغة بين التدريس الأكاديمي والتميز الهندسي البحت.",
            "Colombia": "كولومبيا",
            "Coming Soon": "قريباً",
            "Command": "طلب الخدمة",
            "Command Center": "مركز القيادة",
            "Command Hub": "مركز القيادة",
            "Comms & Intelligence": "الاتصالات والمعلومات",
            "Comms Module": "وحدة الاتصالات",
            "Comoros": "جزر القمر",
            "Complete oversight of your department. Distribute workload evenly, monitor deadline risks, and evaluate quality scores across all team members.": "رقابة كاملة على قسمك. وزع عبء العمل بالتساوي، وراقب مخاطر المواعيد النهائية، وقيم الجودة.",
            "Completed": "مكتمل",
            "Completed (/)": "مكتمل (/)",
            "Completed Tasks": "المهام المكتملة",
            "Completion": "الإنجاز",
            "Completion Rate": "معدل الإنجاز",
            "Completion:": "اكتمال:",
            "Comprehensive vulnerability analysis, network defense modeling, and cryptographic protocols implementation.": "تحليل شامل للثغرات الأمنية، نمذجة الدفاع عن الشبكة، وتطبيق بروتوكولات التشفير.",
            "Computer Science Chair": "رئيس قسم علوم الكمبيوتر",
            "Computer Vision": "الرؤية الحاسوبية",
            "Conferences": "المؤتمرات",
            "Configure": "تكوين",
            "Configure Download": "تكوين التنزيل",
            "Configure Policy": "تكوين السياسة",
            "Configure Task": "تكوين المهمة",
            "Configure standard organizational working hours. These are used to calculate expectations and flag late arrivals.": "تكوين ساعات العمل القياسية للمؤسسة. تُسستخدم هذه لحساب التوقعات وتحديد الوصول المتأخر.",
            "Confirm": "تأكيد",
            "Confirm Action": "تأكيد الإجراء",
            "Confirm Authorization": "تأكيد التفويض",
            "Confirm New Key": "تأكيد المفتاح الجديد",
            "Confirm Receipt": "تأكيد الاستلام",
            "Connect": "اتصل بنا",
            "Connect Live": "اتصال مباشر",
            "Contact Administration": "الاتصال بالإدارة",
            "Context/Description": "السياق/الوصف",
            "Contextual Intelligence": "ذكاء سياقي",
            "Continuous roadmap status access through our proprietary WorkTrack Pro architecture portal.": "الوصول المستمر إلى حالة خارطة الطريق من خلال بوابة الهندسة الخاصة بنا WorkTrack Pro.",
            "Corr.": "المراسلات",
            "Correspondence": "المراسلات",
            "Correspondence Category": "فئة المراسلة",
            "Correspondence Details": "تفاصيل المراسلة",
            "Correspondence Registry": "سجل المراسلات",
            "Correspondence Settings": "إعدادات المراسلة",
            "Correspondence Type": "نوع المراسلة",
            "Corresponding Items": "العناصر المقابلة",
            "Costa Rica": "كوستاريكا",
            "Count of all tasks with": "عدد جميع المهام مع",
            "Country": "البلد",
            "Country Overview": "نظرة عامة على البلد",
            "Country Selection": "اختيار الدولة",
            "Cover Image": "صورة الغلاف",
            "Create Action": "إنشاء إجراء",
            "Create Correspondence": "إنشاء مراسلة",
            "Create Module": "إنشاء وحدة",
            "Create New Account": "إنشاء حساب جديد",
            "Create New Module": "إنشاء وحدة جديدة",
            "Create New Task": "إنشاء مهمة جديدة",
            "Create New Template": "إنشاء قالب جديد",
            "Create New User Account": "إنشاء حساب مستخدم جديد",
            "Create New User Account - Worktrack Pro": "إنشاء حساب مستخدم جديد - وورك تراك برو",
            "Create Task": "إنشاء مهمة",
            "Create Template": "إنشاء القالب",
            "Create User Account": "إنشاء حساب المستخدم",
            "Create a specialized department unit": "إنشاء وحدة قسم متخصصة",
            "Create your first workflow sequence to get started.": "أنشئ أول سلسلة سير عمل للبدء.",
            "Created": "تم الإنشاء",
            "Created At": "أنشئ في",
            "Created by": "تم الإنشاء بواسطة",
            "Critical": "حرج",
            "Critical Alerts": "تنبيهات حرجة",
            "Croatia": "كرواتيا",
            "Cuba": "كوبا",
            "Current Area View": "عرض المنطقة الحالية",
            "Current Institution": "المؤسسة الحالية",
            "Current Readiness": "الجاهزية الحالية",
            "Current Total": "الإجمالي الحالي",
            "Current:": "الحالي:",
            "Currently Selected:": "المحدد حالياً:",
            "Custom Field Data": "بيانات الحقول المخصصة",
            "Custom Interval": "فترة مخصصة",
            "Custom Polygon / Grid": "مضلع مخصص / شبكة",
            "Custom Web Applications": "تطبيقات ويب مخصصة",
            "Custom high-performance websites: digital storefronts, e-commerce networks, and high-conversion system landing pages.": "مواقع إلكترونية مخصصة عالية الأداء: واجهات رقمية، شبكات تجارة إلكترونية، وصفحات هبوط عالية التحويل.",
            "Custom web applications": "تطبيقات ويب مخصصة",
            "Cybersecurity & Hardening": "الأمن السيبراني وتحصين الأنظمة",
            "Cyprus": "قبرص",
            "Czech Republic": "جمهورية التشيك",
            "DEC": "ديسمبر",
            "DEGHA": "دغة",
            "DEGHA Houssem Eddine": "دغة حسام الدين",
            "DEGHA Houssem Eddine Portfolio": "ملف أعمال دغة حسام الدين",
            "DEGHA’s expertise spans various domains of computer science, including Artificial Intelligence, Information Technology, Software Development, Web Development, Database Management, and Networking. He holds advanced skills in Desktop Application Development, Deep Learning, Natural Language Processing (NLP), Recommendation Systems, and Energy Efficiency. He excels in problem-solving and optimizing complex operations.": "تمتد خبرة دغة عبر مجالات مختلفة من علوم الكمبيوتر، بما في ذلك الذكاء الاصطناعي وتكنولوجيا المعلومات وتطوير البرمجيات وتطوير الويب وإدارة قواعد البيانات والشبكات. وهو يمتلك مهارات متقدمة في تطوير تطبيقات سطح المكتب، التعلم العميق، معالجة اللغة الطبيعية (NLP)، أنظمة التوصية، وكفاءة الطاقة. ويتميز في حل المشكلات وتحسين العمليات المعقدة.",
            "DEPARTMENTS": "الأقسام",
            "DEPLOYED / ACTIVE": "منشور / نشط",
            "DHE_CORE // AI_SYSTEM_INIT": "DHE_CORE // تهيئة نظام الذكاء الاصطناعي",
            "DR Congo": "جمهورية الكونغو الديمقراطية",
            "Daily Attendance": "الحضور اليومي",
            "Dark Mode": "الوضع الداكن",
            "Dashboard": "لوحة التحكم",
            "Data Approved": "تمت الموافقة على البيانات",
            "Data Integrity & Real-time Sync": "سلامة البيانات والمزامنة الفورية",
            "Data Rejected": "تم رفض البيانات",
            "Database Architecture & Tuning": "بنية وضبط قواعد البيانات",
            "Database Models": "نماذج قواعد البيانات",
            "Database access": "الوصول لقاعدة البيانات",
            "Date": "التاريخ",
            "Date Joined": "تاريخ الانضمام",
            "Dates": "التواريخ",
            "Day": "يوم",
            "Days": "أيام",
            "Days Absent": "أيام الغياب",
            "Days Left (High to Low)": "الأيام المتبقية (من الأعلى للأقل)",
            "Days Present": "أيام الحضور",
            "Deadline": "الموعد النهائي",
            "Deadline view": "عرض المواعيد النهائية",
            "Deadline:": "الموعد النهائي:",
            "Dec 31": "31 ديسمبر",
            "Decision": "قرار",
            "Dedicated Contexts": "بيئات عمل مخصصة",
            "Deep learning pipelines integrated with econometric estimators for causal health policy predictions.": "خطوط أنابيب التعلم العميق المتكاملة مع المقدرات الاقتصادية القياسية للتنبؤ بالسياسات الصحية السببية.",
            "Deep-learning medical imaging workflow parsing brain MRI files and highlighting abnormal neural growth structures with pixel-level segmentation boundaries.": "سير عمل التصوير الطبي بالتعلم العميق لتحليل ملفات الرنين المغناطيسي للدماغ وتسليط الضوء على هياكل النمو العصبي غير الطبيعية مع حدود تقسيم على مستوى البكسل.",
            "DeepWater Oceanic Telemetry Node": "ديب ووتر عقدة القياس المحيطي عن بعد",
            "DeepWater Oceanic telemetry Node": "ديب ووتر عقدة القياس المحيطي عن بعد",
            "Define Rectangular Area": "تحديد منطقة مستطيلة",
            "Define a custom boundary by drawing on the map.": "حدد حدوداً مخصصة عن طريق الرسم على الخريطة.",
            "Define specific fields that workers must fill out when submitting this task (e.g., \"Report Number\", \"Verification Result\", etc.)": "حدد حقولاً معينة يجب على الموظفين ملؤها عند تقديم هذه المهمة (مثل \"رقم التقرير\"، \"نتيجة التحقق\"، إلخ.)",
            "Define the requirements for this unit...": "حدد متطلبات هذه الوحدة...",
            "Definition & Impact": "التعريف والتأثير",
            "Degha Houssem Eddine is an independent software engineer and entrepreneur specializing in industrial digital transformation, advanced web/mobile application architecture, and custom AI solutions.": "دغة حسام الدين هو مهندس برمجيات مستقل ورائد أعمال متخصص في التحول الرقمي الصناعي وبنية تطبيقات الويب والهاتف المحمولة المتقدمة وحلول الذكاء الاصطناعي المخصصة.",
            "Delete": "حذف",
            "Delete Draft": "حذف المسودة",
            "Deliverable Files": "الملفات القابلة للتسليم",
            "Demand Sent!": "تم إرسال الطلب!",
            "Denmark": "الدانمرك",
            "Density Limit": "حد الكثافة",
            "Department": "القسم",
            "Department Punctuality": "انضباط القسم",
            "Department Unit / Module": "وحدة القسم / النموذج",
            "Deploy WorkTrack Pro for your department today.": "ابدأ تشغيل ورك تراك برو لقسمك اليوم.",
            "Deployment Elapsed": "المنقضي من النشر",
            "Deployment Load": "عبء النشر",
            "Deployments": "المُقدَّمة",
            "Depth": "العمق",
            "Depts Synced": "الأقسام المتزامنة",
            "Description": "الوصف",
            "Design reusable workflow sequences that can be deployed instantly as new action plans.": "صمم سلاسل سير عمل قابلة لإعادة الاستخدام يمكن نشرها فوراً كخطط عمل جديدة.",
            "Desktop Logical Apps": "تطبيقات سطح المكتب المنطقية",
            "Desktop logical apps": "تطبيقات سطح المكتب المنطقية",
            "Detailed Audit": "مراجعة تفصيلية",
            "Detailed task description": "وصف تفصيلي للمهمة",
            "Details": "التفاصيل",
            "Developed Client Projects": "مشاريع العملاء المطورة",
            "Developed Projects": "المشاريع المطورة",
            "Development cycles typically range from 2 to 12 weeks depending on complexity. Prototypes are routinely built and demonstrated within 48 hours, and clients track live milestones 24/7 via the WorkTrack Pro portal.": "تتراوح دورات التطوير عادةً من 2 إلى 12 أسبوعاً اعتماداً على التعقيد. يتم بناء النماذج الأولية وعرضها بشكل روتيني في غضون 48 ساعة، ويتتبع العملاء تقدم العمل على مدار الساعة طوال أيام الأسبوع عبر بوابة WorkTrack Pro.",
            "Digital Twin Simulators": "محاكيات التوأم الرقمي",
            "Direct Report (No Manager)": "تقرير مباشر (لا يوجد مدير)",
            "Directive": "توجيه",
            "Directives": "التوجيهات",
            "Discard Changes": "تجاهل التغييرات",
            "Discovery Rate": "معدل الاكتشاف",
            "Discussion": "نقاش",
            "Dismiss": "إغلاق",
            "Distinct, optimized interfaces for Managers, Workers, and Admins to ensure focused productivity.": "واجهات متميزة ومحسنة للمدراء والموظفين والمسؤولين لضمان إنتاجية مركزة.",
            "Django": "دجانغو",
            "Django Admin": "لوحة إدارة جانغو",
            "Djibouti": "جيبوتي",
            "Do I work with international clients?": "هل أعمل مع عملاء دوليين؟",
            "Docker": "دوكر",
            "Document": "مستند",
            "Documentation": "المستندات",
            "Documentation & Media": "الوثائق والوسائط",
            "Doe": "دو",
            "Dominica": "دومينيكا",
            "Dominican Republic": "جمهورية الدومينيكان",
            "Done": "تمت",
            "Done for today": "انتهيت لليوم",
            "Download CSV": "تنزيل CSV",
            "Download Current View": "تنزيل العرض الحالي",
            "Download Depth": "عمق التنزيل",
            "Download full regions and batch sync task locations for offline use.": "تنزيل مناطق كاملة ومزامنة مواقع المهام دفعة واحدة للاستخدام بدون اتصال بالإنترنت.",
            "Downloading Area...": "جاري تنزيل المنطقة...",
            "Downloading large areas at high zoom levels can consume Gigabytes of storage and significant internet data. Use Wi-Fi when syncing large regions.": "قد يؤدي تنزيل مناطق كبيرة بمستويات تكبير عالية إلى استهلاك غيغابايت من مساحة التخزين وبيانات إنترنت كبيرة. استخدم شبكة Wi-Fi عند مزامنة مناطق كبيرة.",
            "Dr. Ahmed M.": "د. أحمد م.",
            "Dr. DEGHA HOUSSEM EDDINE": "د. دغة حسام الدين",
            "Dr. DEGHA HOUSSEM EDDINE. All Rights Reserved.": "د. دغة حسام الدين. جميع الحقوق محفوظة.",
            "Dr. Degha Houssem Eddine": "د. دغة حسام الدين",
            "Dr. Degha developed an incredibly fast e-commerce backend integrated with a custom inventory-sync worker that solved our concurrency bottlenecks.": "طور د. دغة واجهة خلفية للتجارة الإلكترونية سريعة بشكل مذهل مدمجة مع عامل مزامنة مخزون مخصص حل اختناقات التزامن لدينا.",
            "Dr. Degha is a Category A Associate Professor, integrating peer-reviewed rigor with enterprise code.": "د. دغة هو أستاذ محاضر من الفئة أ، يدمج الدقة الأكاديمية مع كود الإنتاج للمؤسسات.",
            "Draft": "مسودة",
            "Draft Budget Report v2": "مسودة تقرير الميزانية v2",
            "Drag files here or click to upload": "اسحب الملفات هنا أو انقر للتحميل",
            "Drag-drop tasks": "مهام بالسحب والإفلات",
            "Drop items here or use the form to add units": "أفلت العناصر هنا أو استخدم النموذج لإضافة الوحدات",
            "Dropdown Select": "قائمة منسدلة",
            "Due": "مستحق",
            "Due ASAP": "مستحق في أقرب وقت",
            "Due Date": "تاريخ الاستحقاق",
            "Dynamic Submission Form (Google Form Style)": "نموذج تقديم ديناميكي (نمط نماذج جوجل)",
            "Dynamic thermo-agent environments like Open-SBS to test and optimize building energy footprint.": "بيئات الوكيل الحراري الديناميكية مثل Open-SBS لاختبار وتحسين بصمة الطاقة للمباني.",
            "E-commerce Founder": "مؤسس تجارة إلكترونية",
            "EFFICIENCY": "الكفاءة",
            "EVERY": "كل",
            "EXISTING ATTACHMENTS": "المرفقات الحالية",
            "EXPERIMENTAL": "تجريبي",
            "Econometric causal model analyzing stock market alpha indicators and performing portfolio asset optimization adjustments.": "نموذج سببي اقتصادي قياسي يحلل مؤشرات ألفا لسوق المال ويجري تعديلات تحسين أصول المحفظة.",
            "Ecuador": "الإكوادور",
            "Edit": "تعديل",
            "Edit Correspondence": "تعديل المراسلة",
            "Edit Details": "تعديل التفاصيل",
            "Edit Group": "تعديل المجموعة",
            "Edit Landing & Bio": "تعديل الصفحة الرئيسية والسيرة",
            "Edit Module": "تعديل الوحدة",
            "Edit Task": "تعديل المهمة",
            "Edit Template": "تعديل القالب",
            "Egypt": "مصر",
            "El Salvador": "السلفادور",
            "Elasticsearch": "إلاستيك سيرش",
            "Elena R.": "إيلينا ر.",
            "Email": "البريد الإلكتروني",
            "Email Address": "عنوان البريد الإلكتروني",
            "Email Notifications": "إشعارات البريد",
            "Embedded Systems & IoT": "الأنظمة المدمجة وإنترنت الأشياء",
            "Embedded system firmware for deep sea pressure, salinity, and acoustic sensors transmitting via low-power satellite links.": "برمجيات الأنظمة المدمجة لأجهزة استشعار ضغط المياه العميقة والملوحة والصوتية التي ترسل عبر روابط فضائية منخفضة الطاقة.",
            "Empowering Studies with": "تمكين الدراسات بـ",
            "Enable Recurring Cycle": "تمكين الدورة المتكررة",
            "End of shift notes (optional)": "ملاحظات نهاية الوردية (اختياري)",
            "End shift": "إنهاء المناوبة",
            "End-to-end telemetry system design from microcontrollers to ontological medical database servers.": "تصميم نظام قياس عن بعد شامل من المتحكمات الدقيقة إلى خوادم قواعد البيانات الطبية الوجودية.",
            "Engineered for Accountability": "مصمم للمساءلة والموثوقية",
            "English": "الإنجليزية",
            "Enroll new user...": "تسجيل مستخدم جديد...",
            "Enrolled Team": "الفريق المسجل",
            "Enrolled Team Members": "أعضاء الفريق المسجلين",
            "Ensure all required fields are completed accurately. The new user will be able to log in immediately after account creation using their email address and the password provided above.": "تأكد من إكمال جميع الحقول المطلوبة بدقة. سيتمكن المستخدم الجديد من تسجيل الدخول فوراً بعد إنشاء الحساب باستخدام بريده الإلكتروني وكلمة المرور المقدمة أعلاه.",
            "Ensure your hours are logged accurately for performance reviews.": "تأكد من تسجيل ساعات عملك بدقة لمراجعات الأداء.",
            "Enter Full Name": "أدخل الاسم الكامل",
            "Enter a strong password": "أدخل كلمة مرور قوية",
            "Enter task title": "أدخل عنوان المهمة",
            "Enterprise SaaS": "برمجيات كخدمة للمؤسسات",
            "Enterprise Secure": "مؤسسة آمنة",
            "Enterprise Security": "أمن المؤسسات",
            "Enterprise Task Management": "إدارة مهام المؤسسات",
            "Enterprise-grade task management and workforce precision platform.": "منصة إدارة المهام والدقة الوظيفية للمؤسسات.",
            "Entity Affected": "الكيان المتأثر",
            "Environment Theme": "سمة البيئة",
            "Equatorial Guinea": "غينيا الاستوائية",
            "Eritrea": "إريتريا",
            "Error": "خطأ",
            "Error!": "خطأ!",
            "Est. Download Size": "حجم التنزيل التقريبي",
            "Estimate Area Tiles": "تقدير بلاطات المنطقة",
            "Estimated Cache Size": "حجم التخزين المؤقت المقدر",
            "Estimated Storage": "المساحة التخزينية المقدرة",
            "Estimated Storage Warning": "تحذير المساحة التخزينية المقدرة",
            "Estonia": "إستونيا",
            "Ethiopia": "إثيوبيا",
            "Every destructive or critical action is saved as an immutable JSON string in the database, preventing historical tampering.": "يتم حفظ كل إجراء حرج كسلسلة JSON غير قابلة للتغيير في قاعدة البيانات.",
            "Every status change, assignment, and review is recorded in JSON format for absolute security auditing.": "يتم تسجيل كل تغيير في الحالة والتعيين والمراجعة بتنسيق JSON لضمان أمان التدقيق المطلق.",
            "Excellent Punctuality": "انضباط ممتاز",
            "Execute": "تنفيذ",
            "Execute Diagnostics": "تنفيذ التشخيص",
            "Execution": "التنفيذ والعمل",
            "Executive View": "عرض تنفيذي",
            "Existing Attachments": "المرفقات الموجودة",
            "Expected Clock-in": "الحضور المتوقع",
            "Expected Clock-out": "الانصراف المتوقع",
            "Expert Services": "الخدمات الاحترافية",
            "Explore Modules": "استكشاف الوحدات",
            "Explore Solutions": "استكشف الحلول",
            "Explore real-world applications of scientific engineering, causal machine learning, and workflow management systems.": "اكتشف تطبيقات العالم الحقيقي للهندسة العلمية، التعلم الآلي السببي، وأنظمة إدارة سير العمل.",
            "Explore unpublished modules and expand your tracking capabilities. New assignments are ready for deployment.": "استكشف الوحدات غير المنشورة ووسع إمكانيات التتبع لديك. مهام جديدة جاهزة للنشر.",
            "Export": "تصدير",
            "Export CSV": "تصدير CSV",
            "Export Submissions": "تصدير التقديمات",
            "Export Tasks": "تصدير المهام",
            "Export Tasks CSV": "تصدير المهام بصيغة CSV",
            "Export XLS": "تصدير XLS",
            "FAQ": "الأسئلة الشائعة",
            "FEB": "فبراير",
            "FIELD NAME": "اسم الحقل",
            "FINISHED": "منتهٍ",
            "FastAPI": "فاست إيه بي آي",
            "Fastest": "الأسرع",
            "Favorite |": "المفضلة |",
            "Favorites": "المفضلة",
            "Features": "المميزات",
            "Field Label": "عنوان الحقل",
            "Field Label (Question)": "تسمية الحقل (السؤال)",
            "Field Type": "نوع الحقل",
            "Figma": "فيجما",
            "Fiji": "فيجي",
            "File Name": "اسم الملف",
            "File Upload": "تحميل الملف",
            "Filter": "تصفية",
            "Filter by status": "تصفية حسب الحالة",
            "Filter:": "تصفية:",
            "Final Score": "النقاط النهائية",
            "Finland": "فنلندا",
            "Firebase": "فايربيز",
            "Firmware engineering for microcontrollers, sensors calibration, and distributed real-time telemetry communication networks.": "هندسة البرمجيات الثابتة للمتحكمات الدقيقة، معايرة أجهزة الاستشعار، وشبكات اتصالات القياس البعيد الموزعة في الوقت الفعلي.",
            "First Name": "الاسم الأول",
            "Fleet Coordinator Hub": "مركز منسق الأسطول",
            "Force Next Cycle Now": "فرض الدورة التالية الآن",
            "Forever": "للأبد",
            "Forgot Password?": "هل نسيت كلمة المرور؟",
            "Forgot password?": "هل نسيت كلمة المرور؟",
            "France": "فرنسا",
            "Frequently Asked Questions": "الأسئلة الشائعة",
            "Fri": "الجمعة",
            "Full Country Sync": "مزامنة البلد بالكامل",
            "Full Details": "التفاصيل الكاملة",
            "Full Page": "صفحة كاملة",
            "Full Transparency": "شفافية كاملة",
            "Fully Acknowledged": "تم الإقرار بالاستلام بالكامل",
            "G-Estimator": "مقدر G",
            "GLOBAL SCOPE": "النطاق العالمي",
            "GTRESS Research Gateway": "بوابة أبحاث جي تريس",
            "Gabon": "الغابون",
            "Gambia": "غامبيا",
            "General Inquiry / Custom Project": "استفسار عام / مشروع مخصص",
            "General Module": "الوحدة العامة",
            "General Organizational": "تنظيمي عام",
            "General Organizational Intelligence": "الذكاء التنظيمي العام",
            "General Secretariat": "الأمانة العامة",
            "Georgia": "جورجيا",
            "Germany": "ألمانيا",
            "Get Directions": "الحصول على الاتجاهات",
            "Ghana": "غانا",
            "GitHub": "جيتهاب",
            "Global": "عام",
            "Global & Country Sync": "مزامنة عالمية ودولية",
            "Global Completed Tasks": "المهام المكتملة عالمياً",
            "Global Completion Rate": "معدل الإنجاز العالمي",
            "Global Map": "الخريطة العالمية",
            "Global Partners": "الشركاء العالميون",
            "Global Search": "البحث العام",
            "Global Settings": "إعدادات عالمية",
            "Global Task Completion": "إكمال المهام عالمياً",
            "Global Temporal Sync [v5.2]": "مزامنة زمنية عالمية [v5.2]",
            "Global role management": "إدارة الأدوار الوظيفية العامة",
            "Go": "جو",
            "Go & gRPC": "Go و gRPC",
            "Good afternoon": "مساء الخير",
            "Good evening": "مساء الخير",
            "Good morning": "صباح الخير",
            "Greece": "اليونان",
            "Group Avg.": "متوسط المجموعة",
            "Guatemala": "غواتيمالا",
            "Guinea": "غينيا",
            "Guinea-Bissau": "غينيا بيساو",
            "Guyana": "غيانا",
            "HIGH / CRITICAL": "عالي / حرج",
            "HOUSSEM EDDINE": "حسام الدين",
            "Haiti": "هايتي",
            "Happy Clients": "العملاء السعداء",
            "Hardware Lead": "مسؤول الأجهزة",
            "High": "عالي",
            "High depth may take longer to download.": "قد يستغرق العمق العالي وقتاً أطول للتنزيل.",
            "High-fidelity mockups, premium aesthetics, glassmorphic layout frameworks, and responsive interactive wireframing.": "نماذج بالحجم الطبيعي عالية الدقة، جماليات متميزة، إطارات تخطيط زجاجية، ومخططات تفاعلية سريعة الاستجابة.",
            "High-frequency telemetry analysis engine built in Rust to process electrical grid loads in real-time, preventing substation failures via neural anomaly warning loops.": "محرك تحليل قياس عن بعد عالي التردد مبني بلغة Rust لمعالجة أحمال الشبكة الكهربائية في الوقت الفعلي، مما يمنع أعطال المحطات الفرعية عبر حلقات الإنذار بالخلل العصبي.",
            "High-performance standalone desktop software leveraging optimized system APIs and multithreaded logic engines.": "برمجيات مستقلة عالية الأداء لسطح المكتب تستفيد من واجهات برمجة تطبيقات النظام المحسنة ومحركات منطقية متعددة الخيوط.",
            "High-throughput electrical substation monitoring system using sub-millisecond stream pipelines and load balancing estimators.": "نظام مراقبة محطات فرعية كهربائية عالي الإنتاجية باستخدام خطوط تدفق البيانات في أجزاء من الملي ثانية ومقدرات موازنة الحمل.",
            "His academic background coupled with real-world engineering precision resulted in a state-of-the-art causal estimator tool that exceeded our initial specs.": "أدت خلفيته الأكاديمية المقترنة بدقة الهندسة في العالم الحقيقي إلى أداة تقدير سببية متطورة فاقت مواصفاتنا الأولية.",
            "Home": "الرئيسية",
            "Honduras": "هندوراس",
            "Host Management": "إدارة المضيفين",
            "Hours": "ساعات",
            "How It Works": "كيف يعمل النظام",
            "How it Works": "كيف يعمل النظام",
            "How long does it take to develop a system with me?": "كم من الوقت يستغرق تطوير نظام معي؟",
            "How many times should this task cycle? (Empty or -1 for forever)": "كم عدد المرات التي يجب أن تتكرر فيها هذه المهمة؟ (فارغ أو -1 للتكرار للأبد)",
            "How much does a custom platform or mobile app development cost?": "كم تبلغ تكلفة تطوير تطبيق الهاتف أو المنصة المخصصة؟",
            "Hub Status": "حالة المحور",
            "Hungary": "المجر",
            "I deliver high-fidelity engineering results that exceed expectations. As your true technical growth partner in the digital era, I support you from initial system architecture to final production deployment, resolving complex bottlenecks to keep your systems running smoothly.": "أقدم نتائج هندسية عالية الدقة تفوق التوقعات. كشريك نمو تقني حقيقي لك في العصر الرقمي، أدعمك من هندسة النظام الأولية إلى النشر النهائي للإنتاج، مع حل الاختناقات المعقدة للحفاظ على تشغيل أنظمتك بسلاسة.",
            "I specialize in Python, advanced AI/ML frameworks (TensorFlow, PyTorch, LangChain), modern high-performance web stacks (Django, Node.js, React, Tailwind CSS), and secure, enterprise-grade Linux server environments.": "أنا متخصص في لغة Python، وأطر الذكاء الاصطناعي والتعلم الآلي المتقدمة (TensorFlow, PyTorch, LangChain)، وحزم الويب الحديثة عالية الأداء (Django, Node.js, React, Tailwind CSS)، وبيئات خوادم Linux الآمنة والمخصصة للمؤسسات.",
            "IDRAK Operations & Task Orchestration": "إدراك لإدارة العمليات وتنسيق المهام",
            "IDRAK Operations Hub": "مركز عمليات إدراك",
            "INITIATE DEPLOYMENT": "بدء النشر",
            "INITIATE SUBMISSION": "بدء التقديم",
            "INTEGRATIONS READY": "عمليات الدمج جاهزة",
            "IT Director": "مدير تكنولوجيا المعلومات",
            "Iceland": "أيسلندا",
            "Icon & Progress": "الأيقونة والتقدم",
            "Immutable Audit Logs": "سجلات تدقيق غير قابلة للتغيير",
            "Immutable audit log search": "البحث في سجل التدقيق غير القابل للتعديل",
            "Impersonation": "انتحال شخصية",
            "Importance multiplier for performance scoring.": "مضاعف الأهمية لتقييم الأداء.",
            "Important Notice": "إشعار هام",
            "In Progress": "قيد العمل",
            "In:": "دخول:",
            "Inactive": "غير نشط",
            "India": "الهند",
            "Indonesia": "إندونيسيا",
            "InfluxDB": "إنفلوكس دي بي",
            "Info": "معلومات",
            "Infrastructure health metrics": "مؤشرات سلامة البنية التحتية",
            "Initialize Heavy Sync (Z0-18)": "بدء المزامنة الثقيلة (Z0-18)",
            "Innovative Project Label": "علامة مشروع مبتكر",
            "Innovative, data-driven AI systems built to optimize industrial procedures and automate deep cognitive tasks.": "أنظمة ذكاء اصطناعي مبتكرة وقائمة على البيانات مبنية لتحسين الإجراءات الصناعية وأتمتة المهام المعرفية العميقة.",
            "Inspect Architecture": "معاينة البنية البرمجية",
            "Inspect Subsystem": "فحص النظام الفرعي",
            "Install Modules": "تثبيت الوحدات",
            "Interfaces tailored specifically to what each role needs to see, and nothing else.": "واجهات مصممة خصيصاً لتناسب احتياجات كل دور وظيفي دون تشتيت.",
            "Iran": "إيران",
            "Iraq": "العراق",
            "Ireland": "أيرلندا",
            "Israel": "إسرائيل",
            "Issue Correspondence": "إصدار المراسلات",
            "Issue First Correspondence": "إصدار أول مراسلة",
            "Issue New Correspondence": "إصدار مراسلات جديدة",
            "Italy": "إيطاليا",
            "JAN": "يناير",
            "JSON Audit Logs": "سجلات تدقيق JSON",
            "JUL": "يوليو",
            "JUN": "يونيو",
            "Jamaica": "جامايكا",
            "Jan 01": "01 يناير",
            "Japan": "اليابان",
            "John": "جون",
            "Jordan": "الأردن",
            "KANBAN MATRIX": "مصفوفة كانبان",
            "KPI Math Model": "النموذج الرياضي لمؤشرات الأداء",
            "KPI Weight": "وزن مؤشر الأداء الرئيسي",
            "Kanban Board": "لوحة كانبان",
            "Kanban Board — WorkTrack Pro": "لوحة كانبان — وورك تراك برو",
            "Karim A.": "كريم أ.",
            "Kasdi Merbah University, Ouargla": "جامعة قاصدي مرباح، ورقلة",
            "Kazakhstan": "كازاخستان",
            "Keep me signed in": "تذكر تسجيل دخولي",
            "Kenya": "كينيا",
            "Kubernetes": "كوبرنيتيس",
            "Kuwait": "الكويت",
            "Kyrgyzstan": "قيرغيزستان",
            "LEAD": "قائد",
            "LIFECYCLE": "دورة الحياة",
            "LIVE CONTROL ROOM": "غرفة التحكم الحية",
            "LONGITUDE": "خط الطول",
            "LOW / MAINT": "منخفض / صيانة",
            "Language / اللغة": "اللغة / Language",
            "Laos": "لاوس",
            "Last 12 Months": "آخر 12 شهرًا",
            "Last Name": "الاسم الأخير",
            "Last Reactivated": "آخر إعادة تفعيل",
            "Last Sync": "آخر مزامنة",
            "Late": "متأخر",
            "Late Arrivals": "الوصول المتأخر",
            "Late Clock-in Tolerance (mins)": "مهلة التأخير في تسجيل الحضور (بالدقائق)",
            "Late Today": "متأخر اليوم",
            "Late Tolerance": "مهلة التأخير",
            "Late clock-in tolerance": "مهلة التأخير في تسجيل الحضور",
            "Late:": "متأخر:",
            "Latency": "الكمون",
            "Latitude": "خط العرض",
            "Latvia": "لاتفيا",
            "Launch Chat": "بدء الدردشة",
            "Launch Dashboard": "تشغيل لوحة التحكم",
            "Launch Diagnostics": "تشغيل التشخيص",
            "Layla J.": "ليلى ج.",
            "Leaflet Maps": "خرائط Leaflet",
            "Learn More": "لمعرفة المزيد",
            "Lebanon": "لبنان",
            "Lectures": "محاضرات",
            "Legal": "القوانين",
            "Lesotho": "ليسوتو",
            "Level 13 to 15": "المستوى 13 إلى 15",
            "Liberia": "ليبيريا",
            "Libya": "ليبيا",
            "Liechtenstein": "ليختنشتاين",
            "Light Mode": "الوضع الفاتح",
            "Linguistic Matrix": "المصفوفة اللغوية",
            "LinkedIn": "لينكد إن",
            "Linux Hardening": "تحصين نظام لينكس",
            "Lithuania": "ليتوانيا",
            "Live Metrics": "المؤشرات المباشرة",
            "Live Processing": "قيد المعالجة",
            "Live View": "عرض مباشر",
            "Loading": "جارٍ التحميل",
            "Loading Map Engine...": "جاري تحميل محرك الخرائط...",
            "Loading...": "جارٍ التحميل...",
            "Location & Map": "الموقع والخريطة",
            "Location Name": "اسم الموقع",
            "Log Out": "تسجيل الخروج",
            "Login As...": "تسجيل الدخول كـ...",
            "Logistics & Intensity": "اللوجستيات والكثافة",
            "Long Text": "نص طويل",
            "Longitude": "خط الطول",
            "Low": "منخفض",
            "Low-power sea-sensor telemetry logger configured with deep sleep routines and robust MQTT fallback caching to withstand physical offline periods.": "مسجل قياسات عن بعد منخفض الطاقة لأجهزة استشعار البحر مهيأ بروتين نوم عميق وتخزين مؤقت MQTT قوي لتحمل فترات انقطاع الاتصال المادية.",
            "Luxembourg": "لوكسمبورغ",
            "MAR": "مارس",
            "MATRIX": "مصفوفة",
            "MAY": "مايو",
            "MED / STABLE": "متوسط / مستقر",
            "MODULES": "الوحدات",
            "Machine learning computer vision classifier accelerating brain scan tumor segmentation and neurological diagnosis reports.": "مصنف الرؤية الحاسوبية بالتعلم الآلي الذي يسرع تقسيم أورام الدماغ وتقارير التشخيص العصبي.",
            "Madagascar": "مدغشقر",
            "Major Absenteeism": "غياب كبير",
            "Malak B.": "ملاك ب.",
            "Malawi": "ملاوي",
            "Malaysia": "ماليزيا",
            "Mali": "مالي",
            "Malta": "مالطا",
            "Manage Access": "إدارة الوصول",
            "Manage Groups": "إدارة المجموعات",
            "Manage Users": "إدارة المستخدمين",
            "Manage Your Workforce with Precision": "إدارة القوى العاملة الخاصة بك بدقة متناهية",
            "Manage multiple system modules at once": "إدارة وحدات النظام المتعددة في وقت واحد",
            "Management": "الإدارة",
            "Manager": "مدير",
            "Manager Dashboard": "لوحة تحكم المدير",
            "Manager Portal": "بوابة المدير",
            "Manager Quality Rating": "تقييم جودة المدير",
            "Managers": "المدراء",
            "Managers allocate tasks with strict deadlines, priority levels, and expected deliverables.": "يقوم المديرون بتخصيص المهام بمواعيد نهائية صارمة، ومستويات أولوية، ومخرجات متوقعة.",
            "Managers review submissions, assign a quality score (1-5), and approve or request revisions.": "يراجع المديرون التسليمات، ويحددون تقييمًا للجودة (1-5)، ويوافقون أو يطلبون مراجعات إضافية.",
            "Map Cache Database": "قاعدة بيانات التخزين المؤقت للخرائط",
            "Map Engine": "محرك الخرائط",
            "Map Hub": "مركز الخرائط",
            "Marine IoT": "إنترنت الأشياء البحري",
            "Master Schedule": "الجدول الرئيسي",
            "Mauritania": "موريتانيا",
            "Mauritius": "موريشيوس",
            "Max": "الحد الأقصى",
            "Max DD": "أقصى تراجع",
            "Max Detail": "أقصى تفصيل",
            "Max Zoom 18 is recommended for detail.": "يوصى بحد أقصى للتكبير 18 لمزيد من التفاصيل.",
            "Med": "متوسط",
            "MedScan Diagnostic Assistant": "ميدسكان المساعد التشخيصي",
            "MedScan Diagnostic System": "نظام ميدسكان التشخيصي",
            "Medical AI": "الذكاء الاصطناعي الطبي",
            "Medium": "متوسط",
            "Member Name": "اسم العضو",
            "Memo": "مذكرة",
            "Memos": "المذكرات",
            "Message / Requirements": "الرسالة / المتطلبات",
            "Messages": "رسائل",
            "Messenger": "المراسلات الفورية",
            "Metric Variable": "متغير المقياس",
            "Mexico": "المكسيك",
            "Microservice system coordinating robotics pathfinders. Uses custom A* mesh route planning algorithms via WebSockets to synchronize active vehicle vectors.": "نظام خدمات مصغرة ينسق مستكشفي مسارات الروبوتات. يستخدم خوارزميات تخطيط مسار شبكة A* مخصصة عبر WebSockets لمزامنة متجهات المركبات النشطة.",
            "Milestone Achieved": "تحقيق معلم",
            "Minimum 8 characters. Use uppercase, lowercase, numbers, and symbols for stronger security.": "الحد الأدنى 8 أحرف. استخدم أحرفاً كبيرة وصغيرة وأرقاماً ورموزاً لأمان أقوى.",
            "Minor Issues": "مشاكل ثانوية",
            "Minutes": "دقائق",
            "Module": "الوحدة",
            "Module Builder: Sequencing workflow units & correspondence.": "منشئ الوحدات: تسلسل وحدات سير العمل والمراسلات.",
            "Module Dashboard": "لوحة تحكم الوحدة",
            "Module Details": "تفاصيل الوحدة",
            "Module Name": "اسم الوحدة",
            "Module Templates": "قوالب الوحدات",
            "Module Templates · Worktrack Pro": "قوالب الوحدات · وورك تراك برو",
            "Module:": "النموذج:",
            "Modules": "وحدات",
            "Moldova": "مولدوفا",
            "Mon": "الاثنين",
            "Mongolia": "منغوليا",
            "Monitor & Track": "مراقبة وتتبع",
            "Monitor, evaluate, and approve task submissions with precision telemetry and real-time processing streams directly from command zero.": "مراقبة وتقييم واعتماد طلبات تقديم المهام باستخدام القياس الدقيق وتدفقات المعالجة في الوقت الفعلي مباشرة من مركز القيادة.",
            "Montenegro": "الجبل الأسود",
            "Month": "الشهر",
            "Months": "أشهر",
            "Morocco": "المغرب",
            "Motion UI": "واجهة مستخدم حركية",
            "Mozambique": "موزمبيق",
            "Msg Config": "تكوين الرسالة",
            "Multi-Agent": "متعدد الوكلاء",
            "Multi-Selection Checkboxes": "خانات اختيار متعددة",
            "My Attendance History": "سجل حضوري الشخصي",
            "My Completed": "مكتملاتي",
            "My Metrics": "مؤشراتي",
            "My Monthly Overview": "نظرتي الشهرية العامة",
            "My Performance": "أدائي الشخصي",
            "My Records Only": "سجلاتي فقط",
            "My Services": "خدماتي",
            "Myanmar": "ميانمار",
            "NEW": "جديد",
            "NO SIGNAL DETECTED IN LOGS": "لم يتم اكتشاف إشارة في السجلات",
            "NODES:": "العقد:",
            "NOV": "نوفمبر",
            "Name": "الاسم",
            "Name & Profile": "الاسم والملف الشخصي",
            "Namibia": "ناميبيا",
            "National Award": "الجائزة الوطنية",
            "National Award Winner": "الفوز بجوائز وطنية",
            "Native and cross-platform mobile environments using optimized, offline-first architectures for responsive performance.": "بيئات تطبيقات هاتفية أصلية ومتعددة المنصات باستخدام بنيات تفضل العمل دون اتصال بالإنترنت لأداء سريع الاستجابة.",
            "Natural Language Processing (NLP) automatically summarizes task outcomes and identifies bottlenecks.": "يقوم معالج اللغة الطبيعية (NLP) بتلخيص نتائج المهام تلقائياً وتحديد العقبات.",
            "Nepal": "نيبال",
            "Netherlands": "هولندا",
            "New Action": "عملية جديدة",
            "New Encryption Key": "مفتاح تشفير جديد",
            "New Module": "وحدة جديدة",
            "New Strategic Action": "إجراء استراتيجي جديد",
            "New Task": "مهمة جديدة",
            "New User": "مستخدم جديد",
            "New Zealand": "نيوزيلندا",
            "Newest First": "الأحدث أولاً",
            "Next": "التالي",
            "Next »": "التالي »",
            "Nicaragua": "نيكاراجوا",
            "Niger": "النيجر",
            "Nigeria": "نيجيريا",
            "No": "لا",
            "No Circulars": "لا توجد تعاميم",
            "No Correspondence Items": "لا توجد عناصر مراسلة",
            "No Department": "لا يوجد قسم",
            "No Results Found": "لم يتم العثور على نتائج",
            "No Target Date": "لا يوجد تاريخ مستهدف",
            "No Team Members Enrolled": "لا يوجد أعضاء فريق مسجلين",
            "No Templates Found": "لم يتم العثور على قوالب",
            "No administrative correspondence has been issued yet.": "لم يتم إصدار أي مراسلات إدارية بعد.",
            "No assignees yet": "لا يوجد مكلفون بعد",
            "No attachments": "لا توجد مرفقات",
            "No detailed description provided for this operational module.": "لم يتم تقديم وصف مفصل لهذه الوحدة التشغيلية.",
            "No enrolled modules": "لا توجد وحدات مسجلة",
            "No enrolled modules.": "لا توجد وحدات مسجلة.",
            "No favorite users yet.": "لا يوجد مستخدمون مفضلون بعد.",
            "No historical versions archived yet.": "لم تتم أرشفة أي إصدارات تاريخية بعد.",
            "No progress reported": "لم يتم الإبلاغ عن أي تقدم",
            "No recent activity found.": "لم يتم العثور على نشاط حديث.",
            "No recent correspondence.": "لا توجد مراسلات حديثة.",
            "No recent tasks.": "لا توجد مهام حديثة.",
            "No records found": "لم يتم العثور على سجلات",
            "No rejected tasks requiring your attention.": "لا توجد مهام مرفوضة تتطلب انتباهك.",
            "No results found": "لم يتم العثور على نتائج",
            "No roadmap lifecycles available.": "لا توجد دورات حياة لخارطة الطريق.",
            "No strategic lifecycles available.": "لا توجد دورات حياة استراتيجية متاحة.",
            "No strategic notes found across modules.": "لم يتم العثور على ملاحظات استراتيجية عبر الوحدات.",
            "No submissions found": "لم يتم العثور على تقديمات",
            "No tasks found. Create one to get started!": "لم يتم العثور على مهام. أنشئ واحدة للبدء!",
            "No tasks with valid latitude/longitude coordinates were found.": "لم يتم العثور على مهام ذات إحداثيات خطوط عرض/طول صالحة.",
            "No users have been late 3 or more times this month.": "لا يوجد مستخدمون تأخروا 3 مرات أو أكثر هذا الشهر.",
            "No workers available": "لا يوجد موظفون متاحون",
            "Nodes": "العقد",
            "North Korea": "كوريا الشمالية",
            "Norway": "النرويج",
            "Not checked": "غير محدد",
            "Note Title": "عنوان الملاحظة",
            "Notes": "الملاحظات",
            "Notice": "إشعار",
            "Notices": "الإشعارات",
            "Notifications": "الإشعارات",
            "Now": "الآن",
            "Number": "رقم",
            "Number of cycles": "عدد الدورات",
            "OCT": "أكتوبر",
            "ON": "تشغيل",
            "OPERATIONAL ROADMAP": "خارطة الطريق التشغيلية",
            "ORCID ID": "معرف ORCID",
            "OVERALL SCORE": "الدرجة الإجمالية",
            "Office End Time": "وقت نهاية العمل",
            "Office Start Time": "وقت بدء العمل",
            "Official": "رسمي",
            "Official Circulars": "تعاميم رسمية",
            "Official Documents": "وثائق رسمية",
            "Official Feedback": "الملاحظات الرسمية",
            "Official Submissions Registry": "سجل التقديمات الرسمي",
            "Official circulars, directives, memos, and notices requiring formal acknowledgement. Your personal correspondence inbox — track, review, and acknowledge. Full oversight for your organisation's administrative communications.": "المنشورات والتوجيهات والمذكرات والإشعارات الرسمية التي تتطلب إقراراً رسمياً بالاستلام. صندوق المراسلات الشخصي الخاص بك — تتبع وراجع وأقر بالاستلام. إشراف كامل على الاتصالات الإدارية لمؤسستك.",
            "Offline (NEW)": "بدون اتصال (جديد)",
            "Offline Map Hub": "مركز الخرائط بدون اتصال",
            "Offline Map Hub · Worktrack Pro": "مركز الخرائط بدون اتصال · وورك تراك برو",
            "Offline Sync": "مزامنة بدون اتصال",
            "Offset": "الإزاحة",
            "Oldest First": "الأقدم أولاً",
            "Oman": "عمان",
            "On Track": "على المسار",
            "On-Time": "في الوقت المحدد",
            "On-Time Rate": "معدل الالتزام بالوقت",
            "Onboarding": "تأهيل",
            "Open": "مفتوح",
            "Open Modules": "الوحدات المفتوحة",
            "Open-SBS Simulator Engine": "محرك محاكاة Open-SBS",
            "Open-SBS Thermodynamic Digital Twin": "توأم Open-SBS الحراري الرقمي",
            "Only managers can move tasks": "المدراء فقط يمكنهم نقل المهام",
            "Operation": "عملية",
            "Operational Center": "المركز التشغيلي",
            "Operational Cleared": "لا توجد مهام",
            "Operational Horizons": "آفاق تشغيلية",
            "Operational Identity Verified": "تم التحقق من الهوية التشغيلية",
            "Operational Roadmap": "خارطة الطريق التشغيلية",
            "Operational Role": "الدور التشغيلي",
            "Operational Status": "الحالة التشغيلية",
            "Operations": "العمليات",
            "Operations Lead": "مسؤول العمليات",
            "Optimal": "مثالي",
            "Optimization": "التحسين",
            "Order Service": "طلب الخدمة",
            "Org Heatmap ()": "خريطة حرارية للمؤسسة ()",
            "Org Status": "حالة المؤسسة",
            "Organization Structure": "الهيكل التنظيمي",
            "Otmane S.": "عثمان س.",
            "Out:": "خروج:",
            "Outline project objectives, timeline constraints, or architectural dependencies...": "حدد أهداف المشروع، أو قيود الجدول الزمني، أو التبعيات الهندسية...",
            "Outline your requirements, mission goals, or timeline...": "حدد متطلباتك، أهداف المهمة، أو الجدول الزمني...",
            "Outline your service request or project requirements. Upload specifications and add your contact details (optional fields are indicated). We will respond with feasibility analysis and timeline within 24 hours.": "حدد طلب الخدمة أو متمتطلبات المشروع. ارفع المواصفات وأضف تفاصيل الاتصال الخاصة بك (الحقول الاختيارية مشار إليها). سنرد بتحليل الجدوى والجدول الزمني في غضون 24 ساعة.",
            "Overall": "الإجمالي",
            "Overall Index": "المؤشر العام",
            "Overall Progress": "التقدم الإجمالي",
            "Overall Task Progress Health": "حالة تقدم المهام العامة",
            "Overdue": "متأخر",
            "Overview": "نظرة عامة",
            "PDF Document": "مستند PDF",
            "PENDING": "معلق",
            "PENDING REVIEWS": "مراجعات معلقة",
            "PORTRAIT: Dr. DEGHA Houssem Eddine": "صورة شخصية: د. دغة حسام الدين",
            "POTENTIAL GAIN": "المكسب المحتمل",
            "PROCESS": "معالجة",
            "PROG": "التقدم",
            "PROJECT STATUS": "حالة المشروع",
            "PULL_DATA": "سحب البيانات",
            "Page": "صفحة",
            "Page 1": "الصفحة 1",
            "Pakistan": "باكستان",
            "Palau": "بالاو",
            "Palestine": "فلسطين",
            "Panama": "بنما",
            "Papua New Guinea": "بابوا غينيا الجديدة",
            "Paragraph / Long Text": "فقرة / نص طويل",
            "Paraguay": "باراغواي",
            "Partner in Innovation": "شريك في الابتكار",
            "Password": "كلمة المرور",
            "Password strength: Create a password...": "قوة كلمة المرور: أنشئ كلمة مرور...",
            "Password strength: Fair": "قوة كلمة المرور: متوسطة",
            "Password strength: Good": "قوة كلمة المرور: جيدة",
            "Password strength: Very Strong": "قوة كلمة المرور: قوية جداً",
            "Password strength: Weak": "قوة كلمة المرور: ضعيفة",
            "Pen Testing": "اختبار الاختراق",
            "Pending": "قيد الانتظار",
            "Pending (/)": "معلق (/)",
            "Pending Acknowledgement": "في انتظار الإقرار",
            "Pending Audit": "في انتظار التدقيق",
            "Pending Responses": "الردود المعلقة",
            "Pending Review": "قيد المراجعة",
            "Pending Submissions": "التقديمات المعلقة",
            "Pending Tasks": "المهام المعلقة",
            "Pending review queues": "قوائم المراجعة المعلقة",
            "Pending...": "معلق...",
            "Performance": "الأداء",
            "Performance & Effort": "الأداء والجهد",
            "Performance Benchmarks": "معايير الأداء",
            "Performance Formula": "معادلة احتساب الأداء",
            "Performance overview": "نظرة عامة على الأداء",
            "Performance scored objectively: 30% Completion, 30% On-Time, 25% Quality Rating, 15% Volume Bonus.": "يتم احتساب الأداء بموضوعية: 30% للإكمال، 30% للالتزام بالوقت، 25% لتقييم الجودة، و 15% للمهام المنجزة الإضافية.",
            "Personal Information": "المعلومات الشخصية",
            "Personal KPI tracking": "تتبع مؤشرات الأداء الشخصية",
            "Personal stats": "إحصائيات شخصية",
            "Personal tasks": "مهام شخصية",
            "Peru": "بيرو",
            "Philippines": "الفلبين",
            "Phone": "هاتف",
            "Phone Number": "رقم الهاتف",
            "Phone Number (Optional)": "رقم الهاتف (اختياري)",
            "Pioneering the intersection of advanced artificial intelligence, industrial digital transformation, and high-performance software architectures.": "ريادة التقاطع بين الذكاء الاصطناعي المتقدم، التحول الرقمي الصناعي، وبنيات البرمجيات عالية الأداء.",
            "Planned Effort": "الجهد المخطط",
            "Please confirm that you have received and read this correspondence.": "يرجى تأكيد أنك استلمت وقرأت هذه المراسلة.",
            "Poland": "بولندا",
            "Portals": "البوابات",
            "Portugal": "البرتغال",
            "PostgreSQL": "بوستجري إس كيو إل",
            "Potential Gain": "مكاسب محتملة",
            "Powered by Redis. Get instant notifications for assignments, approaching deadlines, and review status.": "مدعوم من Redis. احصل على إشعارات فورية للتعيينات والمواعيد النهائية المقتربة وحالة المراجعة.",
            "Present": "حاضر",
            "Present Today": "حاضر اليوم",
            "Present:": "حاضر:",
            "Presets": "العدادات المسبقة",
            "Prev": "السابق",
            "Pricing is modeled custom based on project architecture, complexity, and target timeline. During initial consultation, a thorough scope analysis is carried out to provide a detailed, competitive quote optimized for your specific investment criteria.": "يتم وضع نموذج التسعير بشكل مخصص بناءً على بنية المشروع وتعقيده والجدول الزمني المستهدف. خلال الاستشارة الأولية، يتم إجراء تحليل دقيق للنطاق لتقديم عرض أسعار مفصل وتنافسي ومحسّن لمعايير الاستثمار الخاصة بك.",
            "Primary Document": "المستند الأساسي",
            "Prioritized task lists": "قوائم المهام المرتبة حسب الأولوية",
            "Priority": "الأولوية",
            "Priority:": "الأولوية:",
            "Privacy Policy": "سياسة الخصوصية",
            "Private": "خاص",
            "Pro": "برو",
            "Processing...": "جاري المعالجة...",
            "Product Manager": "مدير المنتج",
            "Production Excellence Hall": "قاعة التميز الإنتاجي",
            "Production IoT Telemetry": "قياس الاتصال اللاسلكي للإنتاج IoT",
            "Productivity Pulse": "نبض الإنتاجية",
            "Prof. David K.": "أ.د. ديفيد ك.",
            "Profile": "الملف الشخصي",
            "Profile & Avatar": "الملف الشخصي والصورة",
            "Progress": "التقدم",
            "Progress:": "التقدم:",
            "Project 01 / AgriPest": "المشروع 01 / أجريبست",
            "Project 02 / Open-SBS": "المشروع 02 / Open-SBS",
            "Project 03 / IDRAK": "المشروع 03 / إدراك",
            "Project 04 / Voltix": "المشروع 04 / فولتيكس",
            "Project 05 / MedScan": "المشروع 05 / ميدسكان",
            "Project 06 / FleetCo": "المشروع 06 / فليت كو",
            "Project 07 / RoboStock": "المشروع 07 / روبو ستوك",
            "Project 08 / DeepWater": "المشروع 08 / ديب ووتر",
            "Project Panel": "لوحة المشروع",
            "Projects": "مشاريع",
            "Proprietary Architecture": "بنية برمجية خاصة",
            "Publications": "المنشورات العلمية",
            "Published Metrics": "المؤشرات المنشورة",
            "PyMuPDF & PyTorch": "PyMuPDF و PyTorch",
            "PyTorch": "باي تورتش",
            "PyTorch & FastAPI": "PyTorch و FastAPI",
            "Python": "بايثون",
            "Python & DoubleML": "Python و DoubleML",
            "Qatar": "قطر",
            "Quality": "الجودة",
            "Quality Assurance Review": "مراجعة ضمان الجودة",
            "Quality Score": "نقاط الجودة",
            "Quality scoring interface": "واجهة تقييم الجودة",
            "Quant Fin": "التمويل الكمي",
            "Quantitative portfolio optimization system that uses Double Machine Learning models to separate true causal alpha triggers from noise, maximizing capital return curves.": "نظام تحسين المحفظة الكمي الذي يستخدم نماذج التعلم الآلي المزدوج لفصل محفزات ألفا السببية الحقيقية عن الضوضاء، مما يزيد من منحنيات عوائد رأس المال.",
            "Queued Ops": "العمليات المعلقة",
            "Quick Action": "إجراء سريع",
            "Quick Tools": "أدوات سريعة",
            "RBAC Controls": "صلاحيات الوصول القائمة على الأدوار",
            "REF:": "مرجع:",
            "RESEARCH EXCELLENCE": "التميز البحثي",
            "REVIEW CENTRAL": "مركز المراجعة",
            "Radio Buttons": "أزرار الاختيار",
            "Rank & Grade": "الرتبة والدرجة",
            "Reactivation Limit": "حد إعادة التنشيط",
            "Read": "مقروء",
            "Read Publications": "قراءة المنشورات",
            "Read feedback from project partners, collaborators, and clients.": "اقرأ التعليقات من شركاء المشروع والتعاون والعملاء.",
            "Read the Methodology": "قراءة منهجية التقييم",
            "Ready to enforce precision?": "هل أنت جاهز لفرض الدقة التنظيمية؟",
            "Ready. Position the map and choose a download option.": "جاهز. حدد موقع الخريطة واختر خيار التنزيل.",
            "Real-Time Alerts": "تنبيهات فورية",
            "Real-time Sync": "مزامنة في الوقت الفعلي",
            "Real-time Tracking": "التتبع الفوري",
            "Real-time routing and collision prevention control system coordinating warehouse automated guided vehicles.": "نظام توجيه والتحكم في منع الاصطدام في الوقت الفعلي ينسق المركبات الموجهة تلقائياً في المستودع.",
            "Recall": "الاستدعاء",
            "Recent Activity": "النشاط الأخير",
            "Recent Correspondence": "المراسلات الحديثة",
            "Recent Tasks": "المهام الأخيرة",
            "Recently Updated": "المحدثة مؤخراً",
            "Recognition: Officially awarded the Innovative Project Label by the National Startup Committee.": "الاعتراف: مُنح رسمياً علامة مشروع مبتكر من قبل اللجنة الوطنية للشركات الناشئة.",
            "Redirecting...": "جاري إعادة التوجيه...",
            "Redis": "ريديس",
            "Reference": "مرجع",
            "Reference Number": "الرقم المرجعي",
            "Regional Download": "تنزيل إقليمي",
            "Regional High Detail": "تفاصيل إقليمية عالية",
            "Register and provision a new user in the system": "تسجيل وتهيئة مستخدم جديد في النظام",
            "Registry": "سجل المستخدمين",
            "Reject & Request Changes": "رفض وطلب تغييرات",
            "Reject Selected": "رفض المحدد",
            "Rejected": "مرفوض",
            "Rejection": "الرفض",
            "Related Task": "مهمة ذات صلة",
            "Relational and NoSQL schemas optimization, query profiling, clustering, caching, and low-latency storage access.": "تحسين مخططات قواعد البيانات العلاجية وغير العلاجية، تحديد خصائص الاستعلام، التجميع، التخزين المؤقت، والوصول ذو الكمون المنخفض للتخزين.",
            "Relative Sequence": "التسلسل النسبي",
            "Reliable, secure, and scalable web platforms built with robust server architectures tailored to your business operations.": "منصات ويب موثوقة وآمنة وقابلة للتوسع مبنية على بنيات خوادم قوية مصممة لتناسب عمليات عملك.",
            "Remaining": "متبقي",
            "Remove": "إزالة",
            "Remove cover image": "إزالة صورة الغلاف",
            "Remove document": "إزالة المستند",
            "Reporting Manager": "المدير المباشر",
            "Reports": "تقارير",
            "Repositories": "مستودعات الكود",
            "Request Access": "طلب صلاحية الدخول",
            "Request Service": "طلب الخدمة",
            "Request Submitted Successfully!": "تم إرسال الطلب بنجاح!",
            "Request custom implementation parameters for your platform.": "طلب معايير تطبيق مخصصة لمنصتك.",
            "Required": "مطلوب",
            "Requirements / Parameters": "المتطلبات / المعايير",
            "Requires Your Ack": "يتطلب إقرارك",
            "Requires ~30GB+ storage. Syncs deep zoom levels for the entire country.": "يتطلب مساحة تخزين تزيد عن 30 جيجابايت. يزامن مستويات تكبير عميقة للدولة بأكملها.",
            "Research Citations": "الاقتباسات البحثية",
            "Research Director": "مدير الأبحاث",
            "Research Platform": "المنصة البحثية",
            "Research Trajectory": "مسار البحث",
            "Reset All Filters": "إعادة تعيين جميع عوامل التصفية",
            "Reset Search": "إعادة تعيين البحث",
            "Reset Seed": "إعادة تعيين البذرة",
            "Resolved": "تم الحل",
            "Resource Attachments": "مرفقات الموارد",
            "Resources": "المصادر",
            "Resubmit Work": "إعادة إرسال العمل",
            "Return Home": "العودة للرئيسية",
            "Return to Admin": "العودة إلى المسؤول",
            "Review": "مراجعة",
            "Review & Rate": "المراجعة والتقييم",
            "Review your visual timeline or deploy this template to a module.": "راجع خطك الزمني المرئي أو انشر هذا القالب في وحدة.",
            "Reviewer Score": "درجة المراجع",
            "Reviewer Score (0-10)": "درجة المراجع (0-10)",
            "RoboStock Engine": "محرك روبو ستوك",
            "RoboStock Portfolio Analyzer": "محلل محفظة روبو ستوك",
            "Robotics": "الروبوتات",
            "Role": "الدور",
            "Role & Contact": "الدور والاتصال",
            "Role-Based Portals": "بوابات مخصصة للأدوار",
            "Romania": "رومانيا",
            "Run Rate: +24%": "معدل التشغيل: +24%",
            "Run your project with complete visibility.": "قم بتشغيل مشروعك برؤية كاملة.",
            "Russia": "روسيا",
            "Rust": "روست",
            "Rust & WebSockets": "Rust و WebSockets",
            "Rwanda": "رواندا",
            "SATELLITE LAYER": "طبقة القمر الصناعي",
            "SECTOR TELEMETRY": "قياسات القطاع",
            "SEP": "سبتمبر",
            "SIGNAL STATUS": "حالة الإشارة",
            "SSO Ready": "جاهز لتسجيل الدخول الموحد",
            "STAFF FORCE": "قوة الموظفين",
            "STATS": "إحصائيات",
            "STATUS": "الحالة",
            "STATUS VERDICT": "حكم الحالة",
            "STATUS: ONLINE // PROTOCOL": "الحالة: متصل // بروتوكول",
            "STRATEGIC ACTIONS": "إجراءات استراتيجية",
            "STRIPS": "شرائط",
            "STRUCTURED LIST": "القائمة المنظمة",
            "SUBMIT WORK": "إرسال العمل",
            "SYSTEM OPERATIONAL • PORTAL SYNC ACTIVE": "النظام يعمل • البوابة متزامنة",
            "SaaS CTO": "المدير التقني لشركة SaaS",
            "Safety": "السلامة",
            "Sahar K.": "سحر ك.",
            "Sat": "السبت",
            "Satellite Map (Esri) Only": "خريطة الأقمار الصناعية فقط",
            "Satellite Only": "أقمار صناعية فقط",
            "Saudi Arabia": "المملكة العربية السعودية",
            "Save": "حفظ",
            "Save & Exit": "حفظ وخروج",
            "Save & Finish": "حفظ وإنهاء",
            "Save Action": "حفظ الإجراء",
            "Save Policies": "حفظ السياسات",
            "Save Settings": "حفظ الإعدادات",
            "Save Template": "حفظ القالب",
            "Save as Draft": "حفظ كمسودة",
            "Save entire wilayas or custom rectangular areas to ensure they are available without internet.": "حفظ ولايات بأكملها أو مناطق مستطيلة مخصصة لضمان توفرها بدون إنترنت.",
            "Saved": "توفير",
            "Scan Metadata...": "مسح البيانات الوصفية...",
            "Scans": "الفحوصات",
            "Schedule": "الجدول الزمني",
            "Schedule Offset": "إزاحة الجدول الزمني",
            "Scientific Precision.": "الدقة العلمية.",
            "Score": "النقاط",
            "Search": "بحث",
            "Search Query": "استعلام البحث",
            "Search contacts...": "البحث في جهات الاتصال...",
            "Search correspondence...": "البحث في المراسلات...",
            "Search modules...": "بحث في الوحدات...",
            "Search icons (e.g. check, edit, paper)...": "ابحث عن الأيقونات (مثل check، edit، paper)...",
            "Search registry...": "بحث في السجل...",
            "Search submissions...": "البحث في التقديمات...",
            "Search tasks, users, modules… (Ctrl+K)": "ابحث عن المهام، المستخدمين، الوحدات... (Ctrl+K)",
            "Search tasks...": "البحث عن المهام...",
            "Search team...": "البحث في الفريق...",
            "Search templates...": "البحث في القوالب...",
            "Search users by name or email across all roles...": "البحث عن المستخدمين بالاسم أو البريد الإلكتروني عبر جميع الأدوار...",
            "Search workflow units by title or description...": "ابحث عن وحدات سير العمل حسب العنوان أو الوصف...",
            "Search...": "بحث...",
            "Secretariat Modules": "وحدات الأمانة العامة",
            "Secretariat Operations": "عمليات الأمانة العامة",
            "Section / Page Break": "فاصل قسم / صفحة",
            "Secure Access": "دخول آمن",
            "Secured by Aether Architecture": "محمي بواسطة بنية إيثر",
            "Security": "الأمان",
            "Security & Hosts": "الأمان والمضيفين",
            "Security Overview": "نظرة عامة على الأمان",
            "Security Settings": "إعدادات الأمان",
            "Select All Categories": "تحديد جميع الفئات",
            "Select All Matching": "تحديد الكل المتطابق",
            "Select Layer to Cache": "اختر الطبقة للتخزين المؤقت",
            "Select Menu": "قائمة الاختيار",
            "Select Service (Optional)": "اختر الخدمة (اختياري)",
            "Select Team Members by Role": "تحديد أعضاء الفريق حسب الدور",
            "Select Unit Icon": "اختر أيقونة الوحدة",
            "Select a sub-directorate to create independent tasks and track dedicated operations.": "اختر إدارة فرعية لإنشاء مهام مستقلة وتتبع عمليات مخصصة.",
            "Select an option": "حدد خياراً",
            "Selected Service": "الخدمة المختارة",
            "Send Demand": "إرسال الطلب",
            "Send Service Demand": "إرسال طلب خدمة",
            "Senegal": "السنغال",
            "Sensors": "حساسات",
            "Serbia": "صربيا",
            "Settings": "الإعدادات",
            "Seychelles": "سيشل",
            "Share to Chat": "مشاركة في الدردشة",
            "Shared": "مشترك",
            "Shift Logged": "تم تسجيل المناوبة",
            "Shift Times": "أوقات الوردية",
            "Short Text": "نص قصير",
            "Showing": "عرض",
            "Showing Page  of": "عرض الصفحة  من",
            "Showing to of": "عرض إلى من",
            "Sierra Leone": "سيراليون",
            "Sign In": "تسجيل الدخول",
            "Sign Out": "تسجيل الخروج",
            "Sign in to the GTRESS Research Gateway.": "سجل الدخول إلى بوابة أبحاث جي تريس.",
            "Singapore": "سنغافورة",
            "Single Checkbox (True/False)": "خانة اختيار مفردة (صح/خطأ)",
            "Single Selection": "تحديد واحد",
            "Site Settings": "إعدادات الموقع",
            "Size": "الحجم",
            "Slovakia": "سلوفاكيا",
            "Slovenia": "سلوفينيا",
            "Smart Analytics": "تحليلات ذكية",
            "Smart Grid Analyst": "محلل شبكة ذكية",
            "Snapshot": "لقطة",
            "Social Channels": "قنوات التواصل الاجتماعي",
            "Somalia": "الصومال",
            "Sophia L.": "صوفيا ل.",
            "South Africa": "جنوب أفريقيا",
            "South Korea": "كوريا الجنوبية",
            "South Sudan": "جنوب السودان",
            "Spain": "إسبانيا",
            "Special module dedicated to reviewing contact form and service request submissions.": "وحدة متخصصة لمراجعة نماذج الاتصال وطلبات الخدمة.",
            "Specialized technical mentoring, data science curriculum development, and deep learning bootcamps for teams.": "توجيه تقني متخصص، تطوير مناهج علوم البيانات، ودورات مكثفة في التعلم العميق للفرق.",
            "Species": "الأنواع",
            "Speedup": "تسريع العمل",
            "Sri Lanka": "سريلانكا",
            "Staff": "الموظفين",
            "Staff Directory": "دليل الموظفين",
            "Standard Task": "مهمة قياسية",
            "Standard Tasks": "المهام القياسية",
            "Standard time workers are expected to clock in. Used to flag \"Late\" arrivals.": "الوقت القياسي المتوقع لتسجيل دخول الموظفين. يُستخدم لتحديد حالات الوصول \"المتأخر\".",
            "Standard time workers are expected to clock out.": "الوقت القياسي المتوقع لانصراف العمال.",
            "Start": "بدء",
            "Start Date": "تاريخ البدء",
            "Start Date:": "تاريخ البدء:",
            "Start Download": "بدء التنزيل",
            "Start New Resubmission": "بدء إعادة تقديم جديدة",
            "Start by adding workflow units in the form below to visualize your process.": "ابدأ بإضافة وحدات سير العمل في النموذج أدناه لتصور عمليتك.",
            "Start shift": "بدء المناوبة",
            "States/s": "الحالات/ثانية",
            "Statistics": "إحصائيات",
            "Status": "الحالة",
            "Status & Priority": "الحالة والأولوية",
            "Status Coverage": "تغطية الحالة",
            "Status:": "الحالة:",
            "Steps": "الخطوات",
            "Stop Download": "إيقاف التنزيل",
            "Storage & Bandwidth Warning": "تحذير التخزين وعرض النطاق الترددي",
            "Storage Limit Warning": "تحذير حد التخزين",
            "Stored Tiles Info": "معلومات البلاطات المخزنة",
            "Strategic": "استراتيجي",
            "Strategic Board": "لوحة استراتيجية",
            "Strategic Intelligence": "الاستخبارات الاستراتيجية",
            "Strategic Notes": "ملاحظات استراتيجية",
            "Streamline your research workflow with precision-driven tools designed to support advanced studies, academic collaboration, and high-impact discovery.": "قم بتبسيط سير عمل أبحاثك باستخدام أدوات قائمة على الدقة ومصممة لدعم الدراسات المتقدمة والتعاون الأكاديمي والاكتشافات عالية الأثر.",
            "Street & Satellite": "شوارع وأقمار صناعية",
            "Street Map (Voyager) Only": "خريطة الشوارع فقط",
            "Street Only": "شوارع فقط",
            "Strict Role-Based Access Control ensures users only interact with data explicitly assigned to their clearance level.": "يضمن نظام RBAC تفاعل المستخدمين فقط مع البيانات المحددة لمستوى تصريحهم.",
            "Subject & Reference": "الموضوع والمرجع",
            "Subjective reviews are a thing of the past. WorkTrack Pro calculates a definitive performance score based on four weighted pillars, ensuring absolute fairness in evaluation.": "التقييمات الشخصية باتت من الماضي. يحتسب ورك تراك برو درجة أداء نهائية بناءً على 4 ركائز.",
            "Submission Details": "تفاصيل التقديم",
            "Submission Fields (Forms)": "حقول التقديم (النماذج)",
            "Submission Matrix": "مصفوفة التقديمات",
            "Submission Notes": "ملاحظات التقديم",
            "Submission Progress": "تقدم التقديم",
            "Submission Progress: %": "تقدم التقديم: %",
            "Submission created": "تم إنشاء التقديم",
            "Submissions": "التقديمات",
            "Submissions - WorkTrack Pro": "التقديمات - وورك تراك برو",
            "Submissions Data": "بيانات التقديمات",
            "Submissions List": "قائمة التقديمات",
            "Submissions Selected": "التقديمات المحددة",
            "Submit": "إرسال",
            "Submit Another Request": "إرسال طلب آخر",
            "Submit Evaluation": "تقديم التقييم",
            "Submit Service Request": "إرسال طلب الخدمة",
            "Submit UpdatesSubmit Completely": "تقديم التحديثات / تقديم بالكامل",
            "Submit Your Work": "تقديم عملك",
            "Submittal Score": "درجة التقديم",
            "Submitted": "تم الإرسال",
            "Submitted By": "مقدم بواسطة",
            "Submitted Date": "تاريخ التقديم",
            "Submitted for review": "تم الإرسال للمراجعة",
            "Submitter": "المقدم",
            "Success": "نجاح",
            "Success Rate": "معدل النجاح",
            "Sudan": "السودان",
            "Sun": "الأحد",
            "Supabase": "سوبابيز",
            "Super Admin": "المشرف العام",
            "Super Admin Dashboard": "لوحة تحكم المشرف العام",
            "Supervised Theses": "الأطروحات المشرف عليها",
            "Supports PDF, Images, Word, ZIP (Total max 50MB)": "يدعم PDF، الصور، Word، ZIP (الحد الأقصى الإجمالي 50 ميجابايت)",
            "Suriname": "سورينام",
            "Swaziland": "سوازيلاند",
            "Sweden": "السويد",
            "Switzerland": "سويسرا",
            "Sync All Task Locations": "مزامنة جميع مواقع المهام",
            "Sync Pulse": "نبض المزامنة",
            "Sync Status": "حالة المزامنة",
            "Sync large-scale background data for offline context.": "مزامنة بيانات الخلفية واسعة النطاق للسياق بدون اتصال بالإنترنت.",
            "Syria": "سوريا",
            "System": "نظام",
            "System Activity Log": "سجل نشاط النظام",
            "System Admin": "إدارة النظام",
            "System Auto": "نظام تلقائي",
            "System Configs": "تكوينات النظام",
            "System Health": "سلامة النظام",
            "System Modules": "وحدات النظام",
            "System Settings": "إعدادات النظام",
            "System Status": "حالة النظام",
            "System Volume": "حجم النظام",
            "System Weight": "الثقل في النظام",
            "System activity": "نشاط النظام",
            "System-Wide Calculation Methodology": "منهجية الحساب على مستوى النظام",
            "System-wide Interactive Overview": "نظرة عامة تفاعلية على مستوى النظام",
            "System-wide oversight. Manage roles, investigate audit logs, and monitor infrastructure health from a single command center.": "إشراف شامل على النظام. أدر الأدوار، وابحث في سجلات التدقيق، وراقب حالة البنية التحتية.",
            "TASKS": "المهام",
            "TERMINAL // OPEN-SBS.EXE": "محطة الطرفية // OPEN-SBS.EXE",
            "TIME UNIT": "وحدة الوقت",
            "TIMESTAMP": "طابع زمني",
            "TITLE": "العنوان",
            "TODAY": "اليوم",
            "TODAY, May 30": "اليوم، 30 مايو",
            "TOTAL": "الإجمالي",
            "TOTAL NODES": "إجمالي العقد",
            "TX/day": "معاملات/يوم",
            "Tactical Volume": "الحجم التكتيكي",
            "Tailwind": "تايلوند",
            "TailwindCSS": "تايلوند سي إس إس",
            "Taiwan": "تايوان",
            "Tajikistan": "طاجيكستان",
            "Tanzania": "تنزانيا",
            "Tarek F.": "طارق ف.",
            "Target Date": "التاريخ المستهدف",
            "Target: 95%": "الهدف: 95%",
            "Task": "مهمة",
            "Task Calendar": "تقويم المهام",
            "Task Completion": "إكمال المهمة",
            "Task Cover Image": "صورة غلاف المهمة",
            "Task Deployment Sector": "قطاع نشر المهام",
            "Task Detail Preview": "معاينة تفاصيل المهمة",
            "Task Details": "تفاصيل المهمة",
            "Task Image": "صورة المهمة",
            "Task Info": "معلومات المهمة",
            "Task Link": "رابط المهمة",
            "Task List": "قائمة المهام",
            "Task Location": "موقع المهمة",
            "Task Location & Mapping": "موقع المهمة ورسم الخرائط",
            "Task Locations Indexed": "مواقع المهام المفهرسة",
            "Task Management": "إدارة المهام",
            "Task Overview": "نظرة عامة على المهام",
            "Task Progress": "تقدم المهمة",
            "Task Status Section": "قسم حالة المهمة",
            "Task Success Rate": "معدل نجاح المهام",
            "Task Title": "عنوان المهمة",
            "Task Views": "عرض المهام",
            "Task Workspace": "مساحة عمل المهمة",
            "Tasks": "المهام",
            "Tasks - WorkTrack Pro": "المهام - وورك تراك برو",
            "Tasks Completed": "المهام المنجزة",
            "Tasks Completed:": "المهام المكتملة:",
            "Tasks Map Telemetry": "قياسات خريطة المهام",
            "Tasks Requiring Action": "مهام تتطلب إجراء",
            "Tasks in Progress": "المهام قيد التنفيذ",
            "Taught Courses": "المواد المدرّسة",
            "Team Analytics": "تحليلات الفريق",
            "Team Attendance Records": "سجلات حضور الفريق",
            "Team Attendance RecordsMy Attendance History": "سجلات حضور الفريق / سجلي الشخصي",
            "Team Daily Status (Today)": "الحالة اليومية للفريق (اليوم)",
            "Team Lead": "قائد الفريق",
            "Team Performance": "أداء الفريق",
            "Team Search: No Matches": "بحث الفريق: لا توجد تطابقات",
            "Team velocity tracking": "تتبع سرعة إنجاز الفريق",
            "Tech Co-founder": "مؤسس تقني مشارك",
            "Technologies Used": "التقنيات المستخدمة",
            "Telemetry": "القياس عن بعد",
            "Telemetry Grid": "شبكة القياس البعيد",
            "Template": "قالب",
            "Template Builder": "منشئ القوالب",
            "Template Description": "وصف القالب",
            "Template Name": "اسم القالب",
            "Templates": "القوالب",
            "TensorFlow": "تنسور فلو",
            "Terms of Service": "شروط الخدمة",
            "Terraform": "تيرافورم",
            "Thailand": "تايلاند",
            "The AgriPest portal drastically improved our detection response times. The mobile Leaflet geo-caching runs perfectly offline in isolated fields.": "حسنت بوابة AgriPest أوقات الاستجابة للكشف بشكل كبير. يعمل التخزين الجغرافي لـ Leaflet على الهاتف بشكل مثالي دون اتصال بالإنترنت في الحقول المعزولة.",
            "The KPI Mathematical Model": "النموذج الرياضي لمؤشرات الأداء",
            "The Voltix AI Smart Grid telemetry node is amazingly solid. His code is highly optimized, secure, and very clean. Excellent execution.": "إن عقدة القياس عن بعد لشبكة فولتيكس الذكية متينة بشكل مذهل. كوده محسن للغاية وآمن ونظيف للغاية. تنفيذ ممتاز.",
            "The WorkFlow Lifecycle": "دورة حياة سير العمل",
            "The WorkTrack Pro platform gave us complete transparency on milestones. The system was delivered ahead of schedule, and the code quality is absolutely stellar.": "منحتنا منصة WorkTrack Pro شفافية كاملة في مراحل المشروع. تم تسليم النظام قبل الجدول الزمني، وجودة الكود ممتازة للغاية.",
            "The bioinformatics pipelines designed by Dr. Degha are both highly efficient and perfectly documented. He bridges science and code seamlessly.": "تتميز خطوط أنابيب المعلوماتية الحيوية التي صممها د. دغة بالكفاءة العالية والتوثيق الممتاز. إنه يربط بين العلم والكود بسلاسة.",
            "The embedded firmware loop he built for our industrial sensor hubs has reduced power consumption by 40%, enabling long-term off-grid telemetry.": "أدت حلقة البرامج الثابتة المدمجة التي بناها لمحاور أجهزة الاستشعار الصناعية لدينا إلى تقليل استهلاك الطاقة بنسبة 40%، مما أتاح القياس عن بعد طويل المدى خارج الشبكة.",
            "The enterprise-grade task management system designed for the General Secretariat. Delivering immutable audit logs, mathematical KPI modeling, and role-based portal access.": "نظام إدارة المهام المخصص للأمانة العامة. يضمن سجلات تدقيق غير قابلة للتعديل، ونمذجة رياضية للمؤشرات الأساسية، وصلاحيات دخول مخصصة للأدوار.",
            "The real-time telemetry systems and Kubernetes auto-deployment configurations have maintained 100% uptime under extreme workloads.": "حافظت أنظمة القياس عن بعد في الوقت الفعلي وتكوينات النشر التلقائي لـ Kubernetes على وقت تشغيل بنسبة 100% في ظل أعباء العمل القصوى.",
            "There are no attendance logs matching your current filters.": "لا توجد سجلات حضور تطابق التصفية الحالية.",
            "There are no workers officially subscribed to this specific module yet.": "لا يوجد عمال مسجلون رسمياً في هذه الوحدة المحددة بعد.",
            "This action cannot be undone.": "هذا الإجراء لا يمكن التراجع عنه.",
            "This calculation excludes archived modules and is updated instantly as work progresses. The formula ensures that management has an accurate bird's-eye view of the entire operation's efficiency across all departments.": "يستبعد هذا الحساب الوحدات المؤرشفة ويتم تحديثه فورياً مع تقدم العمل. تضمن الصيغة حصول الإدارة على نظرة شاملة ودقيقة لكفاءة العمليات بأكملها عبر جميع الأقسام.",
            "This color will be used visually for this template icon.": "سيتم استخدام هذا اللون بصرياً لأيقونة هذا القالب.",
            "This email will be used as the login username for system access": "سيتم استخدام هذا البريد الإلكتروني كاسم مستخدم لتسجيل الدخول للوصول إلى النظام",
            "This module doesn't have any tasks scheduled yet. Start by creating your first workflow assignment.": "لا تحتوي هذه الوحدة على أي مهام مجدولة بعد. ابدأ بإنشاء تعيين سير العمل الأول.",
            "Thu": "الخميس",
            "Tile Caching Tips": "نصائح التخزين المؤقت للبلاطات",
            "Tile Storage Count": "عدد بلاطات التخزين",
            "Time": "الوقت",
            "Timeline Scale": "مقياس الخط الزمني",
            "Times Late": "مرات التأخير",
            "Timestamp": "الوقت",
            "Title": "العنوان",
            "Today's Focus": "التركيز اليومي",
            "Today's Status:": "حالة اليوم:",
            "Todo": "قائمة المهام",
            "Toggle Todo Panel": "تبديل لوحة المهام",
            "Togo": "توغو",
            "Topic": "الموضوع",
            "Total Assignments": "إجمالي المهام",
            "Total Hours": "إجمالي الساعات",
            "Total Items": "إجمالي العناصر",
            "Total KPI Records": "إجمالي سجلات مؤشرات الأداء",
            "Total Maximum Score": "الدرجة القصوى الإجمالية",
            "Total Missions": "إجمالي المهمات",
            "Total System Assignments": "إجمالي مهام النظام",
            "Total Task Markers": "إجمالي علامات المهام",
            "Total Templates": "إجمالي القوالب",
            "Total expected time to complete this task.": "إجمالي الوقت المتوقع لإكمال هذه المهمة.",
            "Track every iteration of submitted work. Never lose history of revisions, feedback, or attached files.": "تتبع كل تعديل على العمل المقدم. لا تفقد أبداً سجل المراجعات أو الملاحظات أو الملفات المرفقة.",
            "Track your daily shift": "تتبع ورديتك اليومية",
            "Track your daily shift, view personal history, and manage attendance policies.": "تتبع نوبتك اليومية، واعرض سجلك الشخصي، وإدارة سياسات الحضور.",
            "Tracking (NEW)": "التتبع (جديد)",
            "Tracking Mode": "وضع التتبع",
            "Training & Teaching / Mentorship": "التدريب والتعليم / التوجيه",
            "Training & teaching": "التدريب والتعليم",
            "Transparent breakdown of how global efficiency and completion values are aggregated across all active modules.": "تفصيل شفاف لكيفية تجميع قيم الكفاءة والإنجاز العالمية عبر جميع الوحدات النشطة.",
            "Try different search terms or clear your filter.": "جرب مصطلحات بحث مختلفة أو امسح الفلتر.",
            "Tue": "الثلاثاء",
            "Tunisia": "تونس",
            "Turkey": "تركيا",
            "Turkmenistan": "تركمانستان",
            "Twitter": "تويتر",
            "Type": "النوع",
            "Type:": "النوع:",
            "UI/UX Design & Prototyping": "تصميم واجهة وتجربة المستخدم والنمذجة",
            "URGENT": "عاجل",
            "Uganda": "أوغندا",
            "Ukraine": "أوكرانيا",
            "Unassigned": "غير معين",
            "Uncategorized": "غير مصنف",
            "Unified control for General Secretariat Operations.": "تحكم موحد لعمليات الأمانة العامة.",
            "Unified control for work tracking and operations": "تحكم موحد لتتبع العمل والعمليات",
            "Unified tactical view for all active organization tasks. Direct command oversight engaged.": "عرض تكتيكي موحد لجميع مهام المؤسسة النشطة. تم تفعيل الإشراف المباشر على القيادة.",
            "Unit Action Plan": "خطة عمل الوحدة",
            "Unit Identity": "هوية الوحدة",
            "United Arab Emirates": "الإمارات العربية المتحدة",
            "United Kingdom": "المملكة المتحدة",
            "United States": "الولايات المتحدة",
            "Units Defined": "الوحدات المحددة",
            "Unlimited": "غير محدود",
            "Upcoming Deadlines": "المواعيد النهائية القادمة",
            "Update": "تحديث",
            "Update Progress": "تحديث التقدم",
            "Update the correspondence details, reassign recipients, and manage acknowledgements.Create an official circular, directive, memo or notice and assign it to the relevant recipients.": "تحديث تفاصيل المراسلات، وإعادة تعيين المستلمين، وإدارة الإقرارات. إنشاء منشور رسمي، أو توجيه، أو مذكرة، أو إشعار وتعيينه للمستلمين المعنيين.",
            "UpdateIssue Correspondence": "تحديث/إصدار المراسلة",
            "Updated At": "حدث في",
            "Upload corrected versions or reference docs": "تحميل نسخ مصححة أو مستندات مرجعية",
            "Upload your results to complete the task.": "قم برفع نتائجك لإكمال المهمة.",
            "Uploaded": "تم الرفع",
            "Uptime": "وقت التشغيل",
            "Uptime SLA": "اتفاقية مستوى الخدمة",
            "Urgency Rank": "درجة الاستعجال",
            "Uruguay": "الأوروغواي",
            "User": "مستخدم",
            "User Attendance View": "عرض حضور المستخدمين",
            "User Management": "إدارة المستخدمين",
            "User Name": "اسم المستخدم",
            "User Registration": "تسجيل المستخدم",
            "User Registry": "سجل المستخدمين",
            "User Roles": "أدوار المستخدمين",
            "Users": "المستخدمين",
            "Uzbekistan": "أوزبكستان",
            "Value": "القيمة",
            "Vanuatu": "فانواتو",
            "Vehicles": "المركبات",
            "Venezuela": "فنزويلا",
            "Verify Portfolio": "التحقق من المحفظة",
            "Verify Telemetry": "التحقق من القياس البعيد",
            "Version Data Archive": "أرشيف بيانات الإصدار",
            "Version Data Archive (Consolidated Data)": "أرشيف بيانات الإصدار (البيانات الموحدة)",
            "Version Deliverables": "تسليمات الإصدار",
            "Version History": "سجل الإصدارات",
            "Version Snapshot": "لقطة الإصدار",
            "Version-Controlled": "التحكم في النسخ والمراجعات",
            "Version-controlled uploads": "رفع الملفات الخاضع للتحكم في النسخ",
            "Version:": "الإصدار:",
            "Vietnam": "فيتنام",
            "View": "عرض",
            "View All": "عرض الكل",
            "View All Modules": "عرض جميع الوحدات",
            "View Archive": "عرض الأرشيف",
            "View Details": "عرض التفاصيل",
            "View Full Workflow": "عرض سير العمل كاملاً",
            "View Interactive Roadmap": "عرض خارطة الطريق التفاعلية",
            "View Mission Matrix": "عرض مصفوفة المهمة",
            "View Report": "عرض التقرير",
            "View Snapshot History Details": "عرض تفاصيل تاريخ اللقطات",
            "View document": "عرض المستند",
            "View image": "عرض الصورة",
            "Viewing historic attendance records for .": "عرض سجلات الحضور التاريخية لـ .",
            "Views": "طرق العرض",
            "Visibility": "الظهور",
            "Voltix AI Smart Grid Platform": "فولتيكس منصة الشبكة الذكية بالذكاء الاصطناعي",
            "Voltix Smart Grid Subsystem": "النظام الفرعي لشبكة فولتيكس الذكية",
            "Volume Bonus": "علاوة حجم المهام",
            "WIPE RESOLVED": "مسح تم حله",
            "WORKER IDENTITY": "هوية العامل",
            "Warning": "تحذير",
            "We couldn't find any tasks matching your current filters or search terms. Try broadening your criteria.": "لم نتمكن من العثور على أي مهام تطابق عوامل التصفية أو مصطلحات البحث الحالية. حاول توسيع معاييرك.",
            "We deliver high-fidelity engineering and scientific consulting tailored to modern technological challenges.": "نقدم استشارات هندسية وعلمية عالية الدقة مصممة خصيصاً لمواجهة التحديات التكنولوجية الحديثة.",
            "WebSockets": "ويب سوكت",
            "Websites": "مواقع إلكترونية",
            "Websites / Landing Pages": "مواقع إلكترونية / صفحات هبوط",
            "Wed": "الأربعاء",
            "Weeks": "أسابيع",
            "Weight": "الوزن",
            "Welcome": "مرحباً بك",
            "Welcome back": "مرحباً بعودتك",
            "Weweb": "وي ويب",
            "What technologies do I use?": "ما هي التقنيات التي أستخدمها؟",
            "Whitelisted IPs and continuous monitoring for unauthorized access attempts from unknown physical locations.": "عناوين IP المعتمدة والمراقبة المستمرة لمحاولات الوصول غير المصرح بها.",
            "Who can see this template?": "من يمكنه رؤية هذا القالب؟",
            "Why Choose My Solutions?": "لماذا تختار حلولي؟",
            "Wilaya (Province)": "الولاية",
            "Wipe All": "مسح الكل",
            "Wipe Resolved": "مسح تم حله",
            "With more than four years of experience as a Computer Science Engineer at the University of Kasdi Merbah - Ouargla, along with additional teaching roles at the University of Ghardaia, DEGHA has demonstrated a strong ability to enhance technical infrastructures and improve workflows, while effectively contributing to the academic community.": "مع أكثر من أربع سنوات من الخبرة كمهندس علوم كمبيوتر في جامعة قاصدي مرباح - ورقلة، إلى جانب أدوار تدريسية إضافية في جامعة غرداية، أظهر دغة قدرة قوية على تعزيز البنى التحتية التقنية وتحسين سير العمل، مع المساهمة بفعالية في المجتمع الأكاديمي.",
            "WooCommerce": "ووكمرس",
            "WordPress": "وردبريس",
            "WorkTrack": "ورك تراك",
            "WorkTrack Pro": "ورك تراك برو",
            "WorkTrack Pro - Secure Access": "ورك تراك برو - دخول آمن",
            "WorkTrack Pro Official Platform": "المنصة الرسمية لبرنامج ورك تراك برو",
            "WorkTrack Pro moves beyond simple to-do lists to provide mathematical certainty and complete auditability for every task completed within the Secretariat.": "يتجاوز ورك تراك برو قوائم المهام البسيطة ليوفر يقينًا رياضيًا وإمكانية تدقيق كاملة لكل مهمة يتم إنجازها داخل الأمانة العامة.",
            "WorkTrack Pro | Enterprise Task Management": "ورك تراك برو | إدارة مهام المؤسسات",
            "WorkTrack Pro | Kinetic Precision": "ورك تراك برو | الدقة الحركية",
            "WORKTRACK": "وورك تراك",
            "WorkTrack Pro™ CORE v1.0": "نواة WorkTrack Pro™ v1.0",
            "WorkTrack Pro™ gives you 24/7 access to development progress, milestones, deliverables, and next steps — exactly as if you had your own in-house tech department running the project.": "يمنحك WorkTrack Pro™ إمكانية الوصول على مدار الساعة طوال أيام الأسبوع إلى تقدم التطوير، والخطوات المهمة، والتسليمات، والخطوات التالية - تمامًا كما لو كان لديك قسم تقني داخلي خاص بك يدير المشروع.",
            "Worker": "موظف",
            "Worker Portal": "بوابة الموظف",
            "Worker Response / Data": "استجابة العامل / البيانات",
            "Worker Workspace": "مساحة عمل الموظف",
            "Workers": "عمال",
            "Workers submit version-controlled files. Time of submission is locked to prevent deadline disputes.": "يقدم الموظفون ملفات خاضعة للتحكم في الإصدارات. ويتم قفل وقت التقديم لتجنب أي نزاعات.",
            "Workflow Complete?": "هل اكتمل سير العمل؟",
            "Working with Dr. Degha was a game-changer. He transformed our manual workflow into an automated system with flawless AI optimization and incredible execution speed.": "كان العمل مع د. دغة بمثابة نقطة تحول. لقد حول سير عملنا اليدوي إلى نظام مؤتمت مع تحسين مثالي للذكاء الاصطناعي وسرعة تنفيذ مذهلة.",
            "World Overview": "نظرة عامة على العالم",
            "X Days Left": "X أيام متبقية",
            "Yassine T.": "ياسين ت.",
            "Years": "سنوات",
            "Years Tech Exp": "سنوات الخبرة التقنية",
            "Yemen": "اليمن",
            "Yes": "نعم",
            "Yes. I collaborate with businesses and research institutions globally, supporting operations with secure remote infrastructure, virtualized deployment environments, and distributed coordination.": "نعم. أتعاون مع الشركات والمؤسسات البحثية على مستوى العالم، ودعم العمليات ببنية تحتية آمنة عن بعد، وبيئات نشر افتراضية، وتنسيق موزع.",
            "You Ack'd": "لقد قمت بالإقرار",
            "You are currently operating as": "أنت تعمل حاليًا كـ",
            "You can edit draft submissions before they are reviewed": "يمكنك تعديل التقديمات المسودة قبل مراجعتها",
            "You can select multiple files.": "يمكنك اختيار ملفات متعددة.",
            "You can upload multiple files. Formats: PDF, DOC, XLS, IMG, etc.": "يمكنك تحميل ملفات متعددة. التنسيقات: PDF، DOC، XLS، IMG، إلخ.",
            "You have completely logged today's hours.": "لقد قمت بتسجيل ساعات اليوم بالكامل.",
            "You receive direct value for your investment: competitive pricing combined with state-of-the-art code quality, verified scientific frameworks, and absolute transparency throughout our collaboration.": "تحصل على قيمة مباشرة لاستثمارك: تسعير تنافسي مدمج بجودة كود متطورة، أطر عمل علمية تم التحقق منها، وشفافية مطلقة طوال فترة تعاوننا.",
            "Your Email": "بريدك الإلكتروني",
            "Your Name": "اسمك",
            "Your Timeline is Empty": "خطك الزمني فارغ",
            "Your parameters have been logged and queued. Dr. Degha will review the architectural dependencies and follow up within 24 hours.": "تم تسجيل معاييرك ووضعها في قائمة الانتظار. سيقوم د. دغة بمراجعة التبعيات الهندسية ومتابعة طلبك في غضون 24 ساعة.",
            "Your requirements have been logged in our secure database. Our administrative review process will analyze feasibility and follow up within 24 hours.": "تم تسجيل متطلباتك في قاعدة بياناتنا الآمنة. سيقوم فريق المراجعة الإدارية لدينا بتحليل الجدوى والمتابعة في غضون 24 ساعة.",
            "Z0-10 | ~500 MB | 15 min": "Z0-10 | ~500 ميجابايت | 15 دقيقة",
            "Z0-13 | ~30 GB | 10 hours": "Z0-13 | ~30 جيجابايت | 10 ساعات",
            "Z0-6 | ~100MB | 5 min": "Z0-6 | ~100 ميجابايت | 5 دقائق",
            "ZOOM": "التكبير",
            "Zambia": "زامبيا",
            "Zero Objectives Found": "لم يتم العثور على أهداف",
            "Zimbabwe": "زيمبابوي",
            "Zoom Level": "مستوى التكبير",
            "Zoom Range": "نطاق التكبير",
            "Zoom Scope": "نطاق التكبير",
            "[SYS] 18,240 thermal agents instantiated.": "[SYS] تم إنشاء 18,240 وكيلاً حراريًا.",
            "[SYS] Initializing multi-agent thermodynamic loop...": "[SYS] تهيئة حلقة ديناميكية حرارية متعددة الوكلاء...",
            "[SYS] Model: Econometric Causal G-Estimator": "[SYS] النموذج: مقدر G السببي للاقتصاد القياسي",
            "absent": "غائب",
            "achieved first place in the Algerian National “My Thesis in 180 Seconds” competition, focusing on digital themes, organized by the Ministry of Higher Education in 2021. He is an accomplished Data Scientist and Developer with over a decade of experience in development and technical training.": "حصل على المرتبة الأولى في المسابقة الوطنية الجزائرية \\",
            "approved": "موافق عليه",
            "back, _": "رجوع، _",
            "biotech": "التكنولوجيا الحيوية",
            "circular": "منشور رسمي",
            "days left": "أيام متبقية",
            "directive": "توجيه",
            "draft": "مسودة",
            "e.g. Assessment Report": "مثال: تقرير التقييم",
            "e.g. Office A, Site B": "مثال: المكتب أ، الموقع ب",
            "e.g. REF/2026/001": "مثال: REF/2026/001",
            "e.g., Client Name": "مثال: اسم العميل",
            "iOS & Android Mobile Apps": "تطبيقات الهاتف iOS وأندرويد",
            "iOS & Android mobile apps": "تطبيقات الهاتف iOS وأندرويد",
            "item in total": "عنصر في المجموع",
            "late": "متأخر",
            "memo": "مذكرة",
            "notice": "إشعار",
            "of": "من",
            "present": "حاضر",
            "rejected": "مرفوض",
            "s last month": "منذ الشهر الماضي",
            "selected": "محدد",
            "selected items": "عناصر محددة",
            "sensors": "حساسات",
            "status.": "حالة.",
            "tasks with location data.": "المهام ذات البيانات الجغرافية.",
            "terminal": "محطة الطرفية",
            "timeline": "الخط الزمني",
            "to": "إلى",
            "user@example.com": "user@example.com",
            "users": "مستخدمين",
            "water": "مياه",
            "© 2026 COPYRIGHT All rights reserved. TO DEGHA Houssem EDDINE. | Contact": "© 2026 جميع الحقوق محفوظة لدغة حسام الدين. | تواصل",
            "© 2026 Dr. DEGHA HOUSSEM EDDINE. All Rights Reserved.": "© 2026 د. دغة حسام الدين. جميع الحقوق محفوظة.",
            "« Prev": "« السابق",
            "↑ 12% this week": "↑ 12% هذا الأسبوع",
            "⚖️ Decision": "⚖️ قرار",
            "✓ Correspondence issued successfully!": "✓ تم إصدار المراسلة بنجاح!",
            "✓ Task saved successfully!": "✓ تم حفظ المهمة بنجاح!",
            "📌 Directive": "📌 توجيه",
            "📝 Memo": "📝 مذكرة",
            "📢 Circular": "📢 منشور رسمي",
            "🔔 Notice": "🔔 إشعار",
            // Module create/edit form translations
            "Configure your module's identity, access control, and specialized units.": "تكوين هوية وحدتك، والتحكم في الوصول، والوحدات المتخصصة.",
            "e.g. Legal Affairs": "مثال: الشؤون القانونية",
            "Quick Start": "البدء السريع",
            "Select Template (Optional)": "اختر قالباً (اختياري)",
            "-- No Template (Start Blank) --": "-- لا يوجد قالب (بدء فارغ) --",
            "Choosing a template will auto-generate its pre-defined tasks sequentially for this module.": "اختيار قالب سيقوم بإنشاء المهام المحددة مسبقًا تلقائيًا بشكل تسلسلي لهذه الوحدة.",
            "Description (Optional)": "الوصف (اختياري)",
            "A brief overview of this module's scope...": "نبذة مختصرة عن نطاق هذه الوحدة...",
            "Module Group (Optional)": "مجموعة الوحدة (اختياري)",
            "-- No Group --": "-- بدون مجموعة --",
            "Select a group to categorize this module on the dashboard.": "اختر مجموعة لتصنيف هذه الوحدة على لوحة التحكم.",
            "Module Color Accent": "لون تمييز الوحدة",
            "This color will be used for banners and buttons in this module.": "سيتم استخدام هذا اللون للافتات والأزرار في هذه الوحدة.",
            "Start Date": "تاريخ البدء",
            "Deadline Target": "الموعد النهائي المستهدف",
            "Progress Value": "قيمة التقدم",
            "START": "البدء",
            "COMPLETED": "مكتمل",
            "Select System Icon": "اختر أيقونة النظام",
            "Selected": "محدد",
            "Choose from 200+ amazing icons to represent this module.": "اختر من بين أكثر من 200 أيقونة مذهلة لتمثيل هذه الوحدة.",
            "Share to Portal": "مشاركة في البوابة",
            "Display this module in the worker portal even if no tasks are assigned.": "عرض هذه الوحدة في بوابة الموظف حتى لو لم تكن هناك مهام معينة.",
            "Open Enrollment": "التسجيل المفتوح",
            "Allow any user to discover and self-enroll in this module and its tasks.": "السماح لأي مستخدم باكتشاف هذه الوحدة ومهامها والتسجيل فيها ذاتيًا.",
            "Privacy & Access Control": "الخصوصية والتحكم في الوصول",
            "Restrict this module to authorized personnel only": "قصر هذه الوحدة على الأفراد المصرح لهم فقط",
            "Favorite Users": "المستخدمون المفضلون",
            "Other Administrators & Managers": "المدراء والمسؤولون الآخرون",
            "Creator Access:": "وصول المنشئ:",
            "Module Banner Image": "صورة لافتة الوحدة",
            "(Optional — shown on dashboard card)": "(اختياري — يظهر على بطاقة لوحة التحكم)",
            "Current Banner": "اللافتة الحالية",
            "Remove current banner image": "إزالة صورة اللافتة الحالية",
            "Click to upload a banner image": "انقر لتحميل صورة لافتة",
            "JPG, PNG, WEBP — recommended: 800×250px or wider": "JPG, PNG, WEBP — الموصى به: 800 × 250 بكسل أو أعرض",
            "Save Module": "حفظ الوحدة",
            // Module dashboard translations
            "Task Completion": "إكمال المهام",
            "Avg Task Progress": "متوسط تقدم المهام",
            "Todo actions": "إجراءات العمل",
            "Manage All": "إدارة الكل",
            "Create New Todo Action": "إنشاء إجراء عمل جديد",
            "What needs to be done?": "ما الذي يجب القيام به؟",
            "ADD BOX": "إضافة صندوق",
            "Creating...": "جاري الإنشاء...",
            "Low Priority": "أولوية منخفضة",
            "Medium Priority": "أولوية متوسطة",
            "High Priority": "أولوية عالية",
            "No Target Date": "لا يوجد تاريخ مستهدف",
            "Active": "نشط",
            "Create Action": "إنشاء الإجراء",
            // Module dashboard banner / actions
            "Command Center": "مركز التحكم",
            "Manage tasks, submissions, and workflow optimizations for this unit.": "إدارة المهام والتقديمات وتحسينات سير العمل لهذه الوحدة.",
            "Toggle Todo Panel": "إظهار/إخفاء لوحة المهام",
            "Create Task": "إنشاء مهمة",
            "Edit Module": "تعديل الوحدة",
            "Leave Module": "مغادرة الوحدة",
            // Stats cards
            "Total Tasks": "إجمالي المهام",
            "Automated Reactivation": "إعادة التفعيل التلقائية",
            "Completion Rate": "معدل الإكمال",
            // Tab navigation
            "Unit Action Plan": "خطة عمل الوحدة",
            "Submissions Registry": "سجل التقديمات",
            "Official Documents": "الوثائق الرسمية",
            "Enrolled Team": "الفريق المسجل",
            // Task panel
            "Task Directory": "دليل المهام",
            "Search tasks...": "بحث عن مهام...",
            "List View": "عرض القائمة",
            "Grid View": "عرض الشبكة",
            // Correspondence callout
            "Administrative Correspondence": "المراسلات الإدارية",
            "View Correspondence Page": "عرض صفحة المراسلات",
            "New Correspondence": "مراسلة جديدة",
            "No correspondence items yet for this module.": "لا توجد مراسلات بعد لهذه الوحدة.",
            // Create Todo Modal ALL-CAPS labels
            "TITLE": "العنوان",
            "DESCRIPTION": "الوصف",
            "PRIORITY": "الأولوية",
            "DUE DATE": "تاريخ الاستحقاق",
            "ATTACHMENTS (MULTI)": "المرفقات (متعددة)",
            "Drag files here or click": "اسحب الملفات هنا أو انقر",
            "Add more details...": "أضف مزيداً من التفاصيل...",
            "Low": "منخفض",
            "Medium": "متوسط",
            "High": "عال",
            // Todo side panel
            "Action Items": "بنود العمل",
            "PENDING": "معلق",
            "TOTAL": "المجموع",
            "All Caught Up!": "كل شيء مكتمل!",
            "No pending action items for this module. Your list is completely clear.": "لا توجد بنود عمل معلقة لهذه الوحدة. قائمتك فارغة تماماً.",
            "No details provided.": "لا توجد تفاصيل.",
            "Toggle Todo Actions": "إظهار/إخفاء إجراءات العمل",
            "View Details": "عرض التفاصيل",
            "Delete": "حذف",
            "Share Module to Chat": "مشاركة الوحدة في المحادثة",
            "Search contacts...": "البحث عن جهات اتصال...",
            "Loading...": "جاري التحميل...",
            "Send": "إرسال",
            // Worker Performance Page
            "PERFORMANCE DASHBOARD": "لوحة الأداء",
            "Joined": "انضم في",
            "Export Full Data": "تصدير البيانات الكاملة",
            "Tasks Completed": "المهام المكتملة",
            "Days Present": "أيام الحضور",
            "Hours Worked": "ساعات العمل",
            "Completion Rate": "معدل الاكتمال",
            "On-Time Comp.": "الالتزام بالمواعيد",
            "Avg Quality Score": "متوسط درجة الجودة",
            "Task vs Attendance Correlation": "الارتباط بين المهام والحضور",
            "6-Month overlap analysis of presence vs task completion.": "تحليل التلاقي بين الحضور وإنجاز المهام على مدى 6 أشهر.",
            "Task Breakdown": "تحليل تقسيم المهام",
            "Current task status distribution.": "توزيع حالة المهام الحالية.",
            "Competency Radar": "رادار الكفاءة",
            "Holistic view of worker skills and performance.": "رؤية شاملة لمهارات الموظف وأدائه.",
            "Recent Submissions History": "سجل عمليات الإرسال الأخيرة",
            "View All": "عرض الكل",
            "Submission Date": "تاريخ التقديم",
            "Score": "الدرجة",
            "No recent submissions found.": "لم يتم العثور على عمليات إرسال حديثة.",
            // Manager Analytics Page
            "Manager Analytics Panel": "لوحة تحليلات المدير",
            "Real-time overview of team performance and module health": "نظرة عامة في الوقت الحقيقي على أداء الفريق وصحة الوحدات",
            "Export Tasks": "تصدير المهام",
            "Export Submissions": "تصدير عمليات الإرسال",
            "Overdue Tasks": "المهام المتأخرة",
            "Pending Tasks": "المهام المعلقة",
            "Completed": "المكتملة",
            "Avg Score / 100": "متوسط الدرجة / 100",
            "Monthly Submission Trend (6 months)": "اتجاه تقديم الطلبات الشهري (6 أشهر)",
            "Module Health Scores": "درجات صحة الوحدات",
            "overdue": "متأخرة",
            "No modules yet.": "لا توجد وحدات بعد.",
            "Team Performance": "أداء الفريق",
            "Worker": "الموظف",
            "Total Subs": "إجمالي الطلبات",
            "Approved": "المعتمدة",
            "Approval Rate": "معدل الموافقة",
            "Avg Score": "متوسط الدرجة",
            "View": "عرض",
            "No workers found.": "لم يتم العثور على موظفين.",
            // Worker Portal
            "Welcome": "مرحباً",
            "back,": "بعودتك،",
            "Your personal tracking center is synced. Focus your effort on the active objectives below. Complete pending tasks carefully to maintain your execution telemetry.": "مركز التتبع الشخصي الخاص بك متزامن. ركز جهدك على الأهداف النشطة أدناه. أكمل المهام المعلقة بعناية للحفاظ على كفاءة أدائك.",
            "JUMP TO TASKS": "الانتقال إلى المهام",
            "ANALYTICS": "التحليلات",
            "TASKS COMPLETE": "المهام المكتملة",
            "PENDING_TASKS": "مهام_معلقة",
            "UNREAD_MSGS": "رسائل_غير_مقروءة",
            "LIFECYCLE": "دورة_الحياة",
            "Regular Tasks": "المهام العادية",
            "Active": "نشطة",
            "Correspondence": "المراسلات",
            "Unread": "غير مقروءة",
            "In Progress": "قيد الإنجاز",
            "Accomplishments": "الإنجازات",
            "Completed": "مكتملة",
            "Action Required": "إجراء مطلوب",
            "My Modules": "وحداتي",
            "Task Directory": "دليل المهام",
            "Submission History": "سجل الإرسال",
            "Resubmission Required": "إعادة الإرسال مطلوبة",
            "Circulars": "التعميمات",
            "Tasks Requiring Action": "مهام تتطلب إجراء",
            "High": "عالي",
            "Low": "منخفض",
            "Med": "متوسط",
            "Created:": "تاريخ الإنشاء:",
            "Due:": "تاريخ الاستحقاق:",
            "Time Elapsed": "الوقت المنقضي",
            "Overall": "إجمالي",
            "Progress": "التقدم",
            "View Task": "عرض المهمة",
            "Open": "فتح",
            "No enrolled modules": "لا توجد وحدات مسجلة",
            "You haven't been assigned to any modules yet.": "لم يتم تعيينك لأي وحدات بعد.",
            "Total Tasks": "إجمالي المهام",
            "Done": "مكتمل",
            "Enter Dashboard": "دخول لوحة القيادة",
            "Dashboard": "لوحة القيادة",
            "COMPLETION": "الاكتمال",
            "No enrolled modules.": "لا توجد وحدات مسجلة.",
            "Objective / Task": "الهدف / المهمة",
            "Execution Progress": "تقدم التنفيذ",
            "Origin Module": "الوحدة الأصلية",
            "Time Horizon": "الإطار الزمني",
            "Operational Status": "حالة التشغيل",
            "Command": "الأمر",
            "Due at:": "الاستحقاق في:",
            "OPEN": "فتح",
            "Zero Objectives Found": "لم يتم العثور على أهداف",
            "Your task directory is currently empty.": "دليل مهامك فارغ حالياً.",
            "Submission Status": "حالة الإرسال",
            "Submitted At": "تاريخ التقديم",
            "Quality Score": "درجة الجودة",
            "Pending Audit": "في انتظار المراجعة",
            "DETAILS": "التفاصيل",
            "Zero Records Found": "لم يتم العثور على سجلات",
            "You haven't submitted any modules for auditing yet.": "لم تقم بتقديم أي وحدات للمراجعة بعد.",
            "Attention: Resubmission Required": "تنبيه: يلزم إعادة الإرسال",
            "Task Title": "عنوان المهمة",
            "Rejection Reason": "سبب الرفض",
            "Rejected On": "تاريخ الرفض",
            "Action": "إجراء",
            "Resubmit": "إعادة الإرسال",
            "No reason provided": "لم يتم تقديم سبب",
            "No rejected tasks requiring your attention.": "لا توجد مهام مرفوضة تتطلب انتباهك.",
            "Official Circulars": "التعميمات الرسمية",
            "Reference": "المرجع",
            "Title": "العنوان",
            "Date Published": "تاريخ النشر",
            "Read": "قراءة",
            "No Circulars": "لا يوجد تعميمات",
            "You have no official correspondence.": "ليس لديك أي مراسلات رسمية.",
            "Discovery Pipeline": "مسار الاكتشاف",
            "Discover New": "اكتشف الجديد",
            "Operational Horizons": "الآفاق التشغيلية",
            "Explore unpublished modules and expand your tracking capabilities. New assignments are ready for deployment.": "استكشف الوحدات غير المنشورة ووسّع قدرات التتبع الخاصة بك. التعيينات الجديدة جاهزة للنشر.",
            "Open Modules": "الوحدات المفتوحة",
            "Potential Gain": "الكسب المحتمل",
            "Available Assignments": "التعيينات المتاحة",
            "Tasks": "المهام",
            "AVAILABLE": "متاح",
            "Join Module": "الانضمام للوحدة",
            "AVAILABILITY": "التوفر",
            "POTENTIAL GAIN": "المكسب المحتمل",
            "Ready to Join": "جاهز للانضمام",
            "Join": "انضمام",
            "STATUS: ": "الحالة: ",
            "PROTOCOL ": "بروتوكول ",
            "No pending tasks right now.": "لا توجد مهام معلقة في الوقت الحالي.",
            "All Caught Up. No recent tasks.": "الكل منجز. لا توجد مهام حديثة.",
            "My Strategic Notes": "ملاحظاتي الاستراتيجية",
            "Draft a new strategic action or note...": "اكتب إجراءً استراتيجياً أو ملاحظة جديدة...",
            "Save Action": "حفظ الإجراء",
            "Editing Mode": "وضع التعديل",
            "Update Action": "تحديث الإجراء",
            "No Strategic Actions": "لا توجد إجراءات استراتيجية",
            "Start drafting notes below to track your efficiency.": "ابدأ في صياغة الملاحظات أدناه لتتبع كفاءتك.",
            "Mark pending": "تحديد كمعلق",
            "Mark complete": "تحديد كمكتمل",
            "Edit": "تعديل",
            "Delete": "حذف",
            "Are you sure you want to delete this action item?": "هل أنت متأكد أنك تريد حذف عنصر الإجراء هذا؟",
            // User Management Page
            "User Command Center": "مركز إدارة المستخدمين",
            "Manage system access, roles, and personnel hierarchy.": "إدارة وصول النظام والأدوار والتسلسل الهرمي للموظفين.",
            "Add New Member": "إضافة عضو جديد",
            "Total Accounts": "إجمالي الحسابات",
            "System Administrators": "مسؤولو النظام",
            "Managers": "المدراء",
            "Departments": "الأقسام",
            "Search by name or email...": "البحث بالاسم أو البريد الإلكتروني...",
            "All Roles": "جميع الأدوار",
            "All Statuses": "جميع الحالات",
            "Active Only": "النشط فقط",
            "Inactive Only": "غير النشط فقط",
            "Reset": "إعادة تعيين",
            "User Information": "معلومات المستخدم",
            "Role": "الدور",
            "Department": "القسم",
            "Hierarchy / Manager": "التسلسل الهرمي / المدير",
            "Status": "الحالة",
            "Actions": "الإجراءات",
            "Not Assigned": "غير معين",
            "Direct Report": "موظف مباشر",
            "Inactive": "غير نشط",
            "Delete Completely": "حذف نهائياً",
            "Edit Profile": "تعديل الملف الشخصي",
            "Deactivate": "إلغاء التنشيط",
            "Activate": "تنشيط",
            "No users found matching your criteria.": "لم يتم العثور على مستخدمين يطابقون معاييرك.",
            "Edit Member Profile": "تعديل الملف الشخصي للعضو",
            "First Name": "الاسم الأول",
            "Last Name": "اسم العائلة",
            "Email Address": "البريد الإلكتروني",
            "Create New": "إنشاء جديد",
            "--- No Department ---": "--- بدون قسم ---",
            "Enter department name...": "أدخل اسم القسم...",
            "Manager / Reports To": "المدير / يقدم التقارير إلى",
            "--- Direct Report (No Manager) ---": "--- بدون مدير ---",
            "Reset Password": "إعادة تعيين كلمة المرور",
            "(Leave blank to keep current)": "(اتركه فارغاً للاحتفاظ بالحالي)",
            "New password...": "كلمة مرور جديدة...",
            "Cancel": "إلغاء",
            "Save Changes": "حفظ التغييرات",
            // Calendar Page
            "Live": "مباشر",
            "Calendar": "التقويم التشغيلي",
            "LIST VIEW": "عرض القائمة",
            "KANBAN": "كانبان",
            "Total Missions": "إجمالي المهمات",
            "Pending Sync": "مزامنة معلقة",
            "Active Deployment": "نشر نشط",
            "Validated": "تم التحقق",
            "Critical Status": "حالة حرجة",
            "Pending": "معلق",
            "Active": "نشط",
            "Completed": "مكتمل",
            "Critical": "حرج",
        }
    };

    const timeTranslations = {
        'January': 'يناير', 'February': 'فبراير', 'March': 'مارس', 'April': 'أبريل', 'May': 'مايو', 'June': 'يونيو',
        'July': 'يوليو', 'August': 'أغسطس', 'September': 'سبتمبر', 'October': 'أكتوبر', 'November': 'نوفمبر', 'December': 'ديسمبر',
        'Jan': 'يناير', 'Feb': 'فبراير', 'Mar': 'مارس', 'Apr': 'أبريل', 'Jun': 'يونيو',
        'Jul': 'يوليو', 'Aug': 'أغسطس', 'Sep': 'سبتمبر', 'Oct': 'أكتوبر', 'Nov': 'نوفمبر', 'Dec': 'ديسمبر',
        'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد',
        'Mon': 'الاثنين', 'Tue': 'الثلاثاء', 'Wed': 'الأربعاء', 'Thu': 'الخميس', 'Fri': 'الجمعة', 'Sat': 'السبت', 'Sun': 'الأحد',
        'a.m.': 'ص', 'p.m.': 'م', 'AM': 'ص', 'PM': 'م', 'am': 'ص', 'pm': 'م',
        'Jan.': 'يناير', 'Feb.': 'فبراير', 'Mar.': 'مارس', 'Apr.': 'أبريل', 'Aug.': 'أغسطس', 'Sep.': 'سبتمبر', 'Oct.': 'أكتوبر', 'Nov.': 'نوفمبر', 'Dec.': 'ديسمبر'
    };

    function translateDateAndMixedText(text) {
        let translated = text;
        // Translate "Page X of Y" to "الصفحة X من Y"
        translated = translated.replace(/Page\s+(\d+)\s+of\s+(\d+)/gi, 'الصفحة $1 من $2');
        // Translate "Page X" to "الصفحة $1"
        translated = translated.replace(/Page\s+(\d+)/gi, 'الصفحة $1');
        // Regex translation for templates select option: "Template Name (5 workflow tasks)"
        translated = translated.replace(/(\d+)\s+workflow\s+tasks/gi, '$1 مهام سير العمل');
        // Regex translation for creator access in module form
        translated = translated.replace(/As the creator, you \((.*?)\) always maintain full visibility and control over this module\./gi, 'بصفتك المنشئ، فإنك ($1) تحتفظ دائمًا برؤية وسيطرة كاملة على هذه الوحدة.');
        // Regex translation for starts/due date prefixes in dashboard
        translated = translated.replace(/Starts:\s*/gi, 'يبدأ: ');
        translated = translated.replace(/Due:\s*/gi, 'مستحق: ');
        // Regex translation for pending action counters in dashboard
        translated = translated.replace(/(\d+)\s+PENDING\s+ACTION(?:S)?/gi, '$1 إجراءات معلقة');
        translated = translated.replace(/ALL\s+CAUGHT\s+UP/gi, 'كل شيء مكتمل');
        // Regex translation for add todo modal prompt
        translated = translated.replace(/Add a reminder or task for the (.*?) team\./gi, 'أضف تذكيرًا أو مهمة لفريق $1.');
        const keys = Object.keys(timeTranslations).sort((a, b) => b.length - a.length);
        for (const en of keys) {
            const ar = timeTranslations[en];
            const escapedEn = en.replace(/\./g, '\\.');
            const regex = new RegExp(`\\b${escapedEn}(?=\\s|$|\\b)`, 'g');
            translated = translated.replace(regex, ar);
        }
        return translated;
    }

    // Load language preference
    let currentLang = localStorage.getItem(LANG_KEY);
    if (!currentLang) {
        currentLang = window.__defaultSystemLanguage || 'ar';
        localStorage.setItem(LANG_KEY, currentLang);
        setLanguageCookie(currentLang);
    }

    function translateNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.parentElement && (
                node.parentElement.classList.contains('lang-en') ||
                node.parentElement.classList.contains('lang-ar') ||
                node.parentElement.classList.contains('material-symbols-outlined') ||
                node.parentElement.classList.contains('material-icons') ||
                node.parentElement.classList.contains('fa') ||
                node.parentElement.classList.contains('fab') ||
                node.parentElement.classList.contains('fas') ||
                node.parentElement.classList.contains('far') ||
                node.parentElement.classList.contains('bi')
            )) {
                return;
            }
            if (!node._originalText) {
                node._originalText = node.nodeValue;
            }
            const originalVal = node._originalText;
            const text = originalVal.trim();
            if (!text) return;

            const normalizedText = text.replace(/\s+/g, ' ');

            if (translations[currentLang]) {
                let translatedVal = null;
                if (translations[currentLang][text]) {
                    translatedVal = translations[currentLang][text];
                } else if (translations[currentLang][normalizedText]) {
                    translatedVal = translations[currentLang][normalizedText];
                } else {
                    // Lowercase fallback lookup
                    const lowerText = text.toLowerCase();
                    const lowerNormalized = normalizedText.toLowerCase();
                    const lowerDictLookup = Object.keys(translations[currentLang]).find(
                        k => k.toLowerCase() === lowerText || k.toLowerCase() === lowerNormalized
                    );
                    if (lowerDictLookup) {
                        translatedVal = translations[currentLang][lowerDictLookup];
                    }
                }

                if (translatedVal !== null) {
                    const leadingWS = originalVal.match(/^\s*/)[0];
                    const trailingWS = originalVal.match(/\s*$/)[0];
                    node.nodeValue = leadingWS + translatedVal + trailingWS;
                    return;
                }
            }

            if (currentLang === 'en' && node._originalText) {
                node.nodeValue = node._originalText;
            } else if (currentLang === 'ar' && text.length > 0) {
                if (!node._originalText) {
                    node._originalText = originalVal;
                }
                const translated = translateDateAndMixedText(text);
                if (translated !== text) {
                    const leadingWS = originalVal.match(/^\s*/)[0];
                    const trailingWS = originalVal.match(/\s*$/)[0];
                    node.nodeValue = leadingWS + translated + trailingWS;
                }
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            // Skip translation inside script tags, style tags, bilingual spans, and icon containers
            if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE' ||
                node.getAttribute('translate') === 'no' ||
                node.classList.contains('lang-en') ||
                node.classList.contains('lang-ar') ||
                node.classList.contains('material-symbols-outlined') ||
                node.classList.contains('material-icons') ||
                node.classList.contains('fa') ||
                node.classList.contains('fab') ||
                node.classList.contains('fas') ||
                node.classList.contains('far') ||
                node.classList.contains('bi')) {
                return;
            }
            // Translate placeholders
            if (node.placeholder && typeof node.placeholder === 'string') {
                const text = node.placeholder.trim();
                const normalizedText = text.replace(/\s+/g, ' ');
                if (translations[currentLang]) {
                    let translatedVal = null;
                    if (translations[currentLang][text]) {
                        translatedVal = translations[currentLang][text];
                    } else if (translations[currentLang][normalizedText]) {
                        translatedVal = translations[currentLang][normalizedText];
                    } else {
                        // Lowercase fallback lookup
                        const lowerText = text.toLowerCase();
                        const lowerNormalized = normalizedText.toLowerCase();
                        const lowerDictLookup = Object.keys(translations[currentLang]).find(
                            k => k.toLowerCase() === lowerText || k.toLowerCase() === lowerNormalized
                        );
                        if (lowerDictLookup) {
                            translatedVal = translations[currentLang][lowerDictLookup];
                        }
                    }

                    if (translatedVal !== null) {
                        if (!node._originalPlaceholder) {
                            node._originalPlaceholder = node.placeholder;
                        }
                        node.placeholder = translatedVal;
                    } else if (currentLang === 'en' && node._originalPlaceholder) {
                        node.placeholder = node._originalPlaceholder;
                    }
                }
            }

            // Translate title attributes
            if (node.title && typeof node.title === 'string') {
                const text = node.title.trim();
                const normalizedText = text.replace(/\s+/g, ' ');
                if (translations[currentLang]) {
                    let translatedVal = null;
                    if (translations[currentLang][text]) {
                        translatedVal = translations[currentLang][text];
                    } else if (translations[currentLang][normalizedText]) {
                        translatedVal = translations[currentLang][normalizedText];
                    } else {
                        // Lowercase fallback lookup
                        const lowerText = text.toLowerCase();
                        const lowerNormalized = normalizedText.toLowerCase();
                        const lowerDictLookup = Object.keys(translations[currentLang]).find(
                            k => k.toLowerCase() === lowerText || k.toLowerCase() === lowerNormalized
                        );
                        if (lowerDictLookup) {
                            translatedVal = translations[currentLang][lowerDictLookup];
                        }
                    }

                    if (translatedVal !== null) {
                        if (!node._originalTitle) {
                            node._originalTitle = node.title;
                        }
                        node.title = translatedVal;
                    } else if (currentLang === 'en' && node._originalTitle) {
                        node.title = node._originalTitle;
                    }
                }
            }

            // Translate specific elements by label text if they are buttons/inputs
            if (node.tagName === 'INPUT' && (node.type === 'button' || node.type === 'submit') && node.value && typeof node.value === 'string') {
                const text = node.value.trim();
                const normalizedText = text.replace(/\s+/g, ' ');
                if (translations[currentLang]) {
                    let translatedVal = null;
                    if (translations[currentLang][text]) {
                        translatedVal = translations[currentLang][text];
                    } else if (translations[currentLang][normalizedText]) {
                        translatedVal = translations[currentLang][normalizedText];
                    } else {
                        // Lowercase fallback lookup
                        const lowerText = text.toLowerCase();
                        const lowerNormalized = normalizedText.toLowerCase();
                        const lowerDictLookup = Object.keys(translations[currentLang]).find(
                            k => k.toLowerCase() === lowerText || k.toLowerCase() === lowerNormalized
                        );
                        if (lowerDictLookup) {
                            translatedVal = translations[currentLang][lowerDictLookup];
                        }
                    }

                    if (translatedVal !== null) {
                        if (!node._originalValueAttr) {
                            node._originalValueAttr = node.value;
                        }
                        node.value = translatedVal;
                    } else if (currentLang === 'en' && node._originalValueAttr) {
                        node.value = node._originalValueAttr;
                    }
                }
            }

            // Recurse children
            for (let child of node.childNodes) {
                try {
                    translateNode(child);
                } catch (e) {
                    console.error("Child translation error:", e);
                }
            }
        }
    }

    function applyDirection() {
        let spanStyleEl = document.getElementById('lang-spans-toggle-style');
        if (!spanStyleEl) {
            spanStyleEl = document.createElement('style');
            spanStyleEl.id = 'lang-spans-toggle-style';
            document.head.appendChild(spanStyleEl);
        }

        if (currentLang === 'ar') {
            document.documentElement.setAttribute('dir', 'rtl');
            document.documentElement.setAttribute('lang', 'ar');
            if (document.body) {
                document.body.classList.add('rtl-mode');
            }
            spanStyleEl.innerHTML = `
                .lang-en { display: none !important; }
                .lang-ar { display: inline !important; }
            `;
            applyRtlStyles();
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
            document.documentElement.setAttribute('lang', 'en');
            if (document.body) {
                document.body.classList.remove('rtl-mode');
            }
            spanStyleEl.innerHTML = `
                .lang-en { display: inline !important; }
                .lang-ar { display: none !important; }
            `;
            removeRtlStyles();
        }

        // Translate title
        if (document.title) {
            const titleText = document.title.trim();
            if (!document._originalTitle) {
                document._originalTitle = document.title;
            }
            if (currentLang === 'ar' && translations['ar'] && translations['ar'][document._originalTitle]) {
                document.title = translations['ar'][document._originalTitle];
            } else if (currentLang === 'en' && translations['en'] && translations['en'][document._originalTitle]) {
                document.title = translations['en'][document._originalTitle];
            } else {
                document.title = document._originalTitle;
            }
        }
    }

    function applyRtlStyles() {
        let styleEl = document.getElementById('rtl-custom-style');
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'rtl-custom-style';
            styleEl.innerHTML = `
                body.rtl-mode .me-auto {
                    margin-left: auto !important;
                    margin-right: 0 !important;
                }
                body.rtl-mode .ms-auto {
                    margin-right: auto !important;
                    margin-left: 0 !important;
                }
                body.rtl-mode .neural-sidebar {
                    border-left: 1px solid rgba(255,255,255,0.05);
                    border-right: none;
                }
                 body.rtl-mode .ns-nav-link.ns-active::before {
                    left: auto;
                    right: 0;
                    border-radius: 4px 0 0 4px;
                }
                body.rtl-mode .rtl-flip {
                    transform: scaleX(-1) !important;
                }
                body.rtl-mode .animate-marquee {
                    animation: marquee-rtl 60s linear infinite;
                }
                @keyframes marquee-rtl {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(50%); }
                }
                body.rtl-mode .ns-pulse-tag, body.rtl-mode .ns-badge {
                    margin-left: 0;
                    margin-right: auto;
                }
                body.rtl-mode .ns-logout {
                    margin-left: 0;
                    margin-right: auto;
                }
                body.rtl-mode .offcanvas {
                    right: auto !important;
                    left: 0 !important;
                    transform: translateX(-100%);
                }
                body.rtl-mode .offcanvas.show {
                    transform: translateX(0);
                }
                /* Floating buttons (Strategic actions toggle) */
                body.rtl-mode .todo-drawer-toggle,
                body.rtl-mode #generalTodoToggle,
                body.rtl-mode #todo-drawer-floating-btn {
                    right: auto !important;
                    left: 30px !important;
                }
                /* Worker portal notes floating button */
                body.rtl-mode .wp-floating-notes-btn {
                    right: auto !important;
                    left: 2rem !important;
                }
                /* Strategic actions / Todo side drawers (Unified Worker, Manager, Admin) */
                body.rtl-mode .section-todo,
                body.rtl-mode #strategicNotesDrawer,
                body.rtl-mode #notesPanel,
                body.rtl-mode .wp-notes-panel {
                    right: auto !important;
                    left: -440px !important;
                    border-left: none !important;
                    border-right: 1px solid #e2e8f0 !important;
                    box-shadow: 10px 0 40px rgba(0, 0, 0, 0.12) !important;
                    transition: left 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
                }
                body.rtl-mode .section-todo.open,
                body.rtl-mode #strategicNotesDrawer.open,
                body.rtl-mode #notesPanel.open,
                body.rtl-mode .wp-notes-panel.open {
                    right: auto !important;
                    left: 0 !important;
                }
                body.rtl-mode .section-todo.minimized,
                body.rtl-mode #strategicNotesDrawer.minimized {
                    transform: none !important;
                    left: -440px !important;
                    right: auto !important;
                }
                body.rtl-mode {
                    transition: padding-left 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
                    padding-right: 0 !important;
                }
                body.rtl-mode.todo-panel-open,
                body.rtl-mode.wp-notes-open {
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                }
                /* Drawer Edge Arrow Button in RTL - arrow looks right to open in Arabic */
                body.rtl-mode .drawer-border-arrow-btn i,
                html[dir="rtl"] .drawer-border-arrow-btn i {
                    transform: none !important;
                }
                body.rtl-mode .wp-notes-panel:not(.open) .drawer-border-arrow-btn {
                    left: auto !important;
                    right: -44px !important;
                    border-radius: 0 22px 22px 0 !important;
                    border-left: none !important;
                    box-shadow: 4px 4px 18px rgba(0, 0, 0, 0.15) !important;
                }
                body.rtl-mode .wp-notes-panel:not(.open) .drawer-border-arrow-btn:hover {
                    right: -48px !important;
                    transform: scale(1.08) !important;
                }
                body.rtl-mode .wp-notes-panel:not(.open) .drawer-border-arrow-btn .icon-close-arrow {
                    display: inline-block !important;
                }
                body.rtl-mode .wp-notes-panel:not(.open) .drawer-border-arrow-btn .icon-open-arrow {
                    display: none !important;
                }
                body.rtl-mode .wp-notes-panel.open .drawer-border-arrow-btn {
                    left: auto !important;
                    right: -22px !important;
                    border-radius: 50% !important;
                    box-shadow: 4px 4px 20px rgba(0, 0, 0, 0.18) !important;
                }
                body.rtl-mode .wp-notes-panel.open .drawer-border-arrow-btn .icon-close-arrow {
                    display: none !important;
                }
                body.rtl-mode .wp-notes-panel.open .drawer-border-arrow-btn .icon-open-arrow {
                    display: inline-block !important;
                }
                /* Search bar and template builder overrides */
                body.rtl-mode .search-wrapper i {
                    left: auto !important;
                    right: 1.25rem !important;
                }
                body.rtl-mode .search-wrapper input {
                    padding-left: 1rem !important;
                    padding-right: 3rem !important;
                }
                body.rtl-mode .task-actions-wrapper {
                    border-left: none !important;
                    border-right: 1px dashed #f1f5f9 !important;
                    padding-left: 0 !important;
                    padding-right: 10px !important;
                }
                body.rtl-mode .task-id-badge {
                    right: auto !important;
                    left: 2px !important;
                }
                body.rtl-mode .seq-num {
                    right: auto !important;
                    left: 4px !important;
                }
                body.rtl-mode .fa-arrow-left,
                body.rtl-mode .fa-arrow-right,
                body.rtl-mode .fa-chevron-left,
                body.rtl-mode .fa-chevron-right {
                    transform: scaleX(-1) !important;
                }
                
                /* All modes: Black text for create menu/module buttons in sidebar */
                .ns-btn-primary,
                .ns-btn-primary *,
                .ns-btn-primary:hover,
                .ns-btn-primary:hover *,
                .neural-sidebar .ns-btn-primary,
                .neural-sidebar .ns-btn-primary *,
                .btn-create-module,
                .btn-create-module *,
                .btn-create-task,
                .btn-create-task * {
                    color: #000000 !important;
                    font-weight: 800 !important;
                }
                
                /* Sidebar language selectors - identical sleek glass pill styling */
                .neural-sidebar #lang-switcher > div,
                .neural-sidebar #top-lang-switcher > div {
                    background: rgba(255, 255, 255, 0.05) !important;
                    border: 1px solid rgba(255, 255, 255, 0.12) !important;
                    border-radius: 9999px !important;
                    box-shadow: none !important;
                }
                .neural-sidebar #lang-switcher > div:hover,
                .neural-sidebar #top-lang-switcher > div:hover {
                    background: rgba(255, 255, 255, 0.12) !important;
                    border-color: rgba(220, 38, 38, 0.6) !important;
                }
                .neural-sidebar #lang-switcher .lang-select,
                .neural-sidebar #top-lang-switcher .lang-select {
                    color: #f8fafc !important;
                    background-color: transparent !important;
                    border: none !important;
                    font-weight: 700 !important;
                }
                .neural-sidebar #lang-switcher .lang-select option,
                .neural-sidebar #top-lang-switcher .lang-select option {
                    color: #000000 !important;
                    background-color: #ffffff !important;
                    font-weight: 700 !important;
                }
                    font-weight: 600 !important;
                    cursor: pointer !important;
                    outline: none !important;
                    transition: all 0.2s !important;
                }
                .global-path-tracker .lang-select,
                #path-lang-switcher .lang-select {
                    color: #0f172a !important;
                    background-color: transparent !important;
                    border: none !important;
                }
                .global-path-tracker .lang-select option,
                #path-lang-switcher .lang-select option {
                    color: #0f172a !important;
                    background-color: #ffffff !important;
                }
                /* Module dashboard RTL hero styles */
                body.rtl-mode .hero-pies-container {
                    right: auto !important;
                    left: 2rem !important;
                }
                body.rtl-mode .hero-icon-orb {
                    right: auto !important;
                    left: 2.5rem !important;
                }
                @media (max-width: 992px) {
                    body.rtl-mode .hero-pies-container {
                        left: 0 !important;
                        margin-right: 0 !important;
                    }
                }
            `;
            document.head.appendChild(styleEl);
        }
    }

    function removeRtlStyles() {
        const styleEl = document.getElementById('rtl-custom-style');
        if (styleEl) styleEl.remove();
    }

    function translateAll() {
        applyDirection();
        if (document.body) {
            translateNode(document.body);
        }
    }

    function injectSwitcher() {
        const containers = document.querySelectorAll('#lang-switcher, .lang-switcher-placeholder');
        containers.forEach(container => {
            if (container.querySelector('.wt-lang')) return; // Already injected
            const group = document.createElement('div');
            group.className = 'wt-lang';
            group.setAttribute('role', 'group');
            group.setAttribute('aria-label', 'Language / اللغة');
            [['en', 'EN', 'English'], ['ar', 'ع', 'العربية']].forEach(([code, label, name]) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.textContent = label;
                btn.title = name;
                btn.setAttribute('lang', code);
                btn.setAttribute('aria-pressed', currentLang === code ? 'true' : 'false');
                btn.addEventListener('click', () => { if (currentLang !== code) switchLanguage(code); });
                group.appendChild(btn);
            });
            container.appendChild(group);
        });
    }

    function switchLanguage(targetLang) {
        currentLang = targetLang;
        localStorage.setItem(LANG_KEY, currentLang);
        setLanguageCookie(currentLang);

        const isLoginPage = window.location.pathname.includes('/login') || window.location.pathname.includes('login');
        const shouldReload = Boolean(window.__forceLanguageReload) === true || 
                             String(window.__forceLanguageReload).toLowerCase() === 'true' || 
                             isLoginPage ||
                             (document.body && document.body.dataset && document.body.dataset.forceReload === 'true');

        if (shouldReload) {
            window.location.reload();
            return;
        }

        translateAll();
        document.querySelectorAll('.wt-lang button').forEach(btn => {
            btn.setAttribute('aria-pressed', btn.getAttribute('lang') === currentLang ? 'true' : 'false');
        });
        window.dispatchEvent(new CustomEvent('languagechange', { detail: { lang: currentLang } }));
    }
    window.switchLanguage = switchLanguage;

    // Run translations
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            injectSwitcher();
            loadDbTranslations();
            translateAll();
            initObserver();
        });
    } else {
        injectSwitcher();
        loadDbTranslations();
        translateAll();
        initObserver();
    }

    function initObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldTranslate = false;
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    shouldTranslate = true;
                }
            });
            if (shouldTranslate) {
                translateAll();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    applyDirection();
    window.translateAll = translateAll;
})();
