"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Mic,
  Brain,
  RefreshCw,
  TrendingUp,
  Clock,
  Users,
  BarChart3,
  MessageSquare,
  Zap,
  Shield,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Play,
  Star,
  Globe,
} from "lucide-react";

// Content translations
const content = {
  en: {
    nav: {
      problem: "The Problem",
      solution: "Solution",
      managers: "For Managers",
      login: "Login",
      cta: "Request Pilot",
    },
    hero: {
      badge: "Enterprise-Grade Sales Intelligence",
      headline: "Turn Every Sales Call into a",
      headlineHighlight: "Growth Opportunity",
      subheadline: "Automated insights, CRM sync, and WhatsApp summaries –",
      subheadlineHighlight: "zero manual entry.",
      ctaPrimary: "Request Pilot",
      ctaSecondary: "Watch Demo",
      socialProof: "Trusted by 50+ sales teams in Israel",
    },
    problem: {
      badge: "The Problem",
      headline: "Your reps are wasting",
      headlineHighlight: "20% of their day",
      headlineSuffix: "on manual CRM updates",
      description: "Every call ends with the same tedious routine: typing notes, updating fields, logging follow-ups. Meanwhile, critical insights slip through the cracks and deals go cold.",
      points: [
        "8+ hours/week lost to manual data entry",
        "Key objections and commitments forgotten",
        "Inconsistent CRM data across the team",
        "Managers flying blind without call visibility",
      ],
      stat: "of selling time lost",
      items: [
        { label: "Manual note-taking", value: "45 min/day" },
        { label: "CRM field updates", value: "30 min/day" },
        { label: "Follow-up scheduling", value: "20 min/day" },
      ],
    },
    solution: {
      badge: "The Solution",
      headline: "From call to CRM in",
      headlineHighlight: "60 seconds",
      description: "Our AI pipeline does the heavy lifting so your reps can focus on what matters: closing deals.",
      steps: [
        {
          step: "01",
          title: "Record",
          description: "Upload or auto-capture sales calls from any source. Hebrew & English supported.",
        },
        {
          step: "02",
          title: "Analyze",
          description: "AI extracts action items, deal values, objections, and next steps instantly.",
        },
        {
          step: "03",
          title: "Sync",
          description: "One-click sync to HubSpot, Priority, or share via WhatsApp. Zero typing.",
        },
      ],
      features: [
        { title: "WhatsApp Summaries", desc: "Share insights in one tap" },
        { title: "Enterprise Security", desc: "SOC 2 compliant, RLS enabled" },
        { title: "Deal Heat Scoring", desc: "AI-powered opportunity ranking" },
        { title: "Hebrew Optimized", desc: "Native Heblish support" },
      ],
    },
    managers: {
      badge: "For Managers",
      headline: "Full visibility into",
      headlineHighlight: "team performance",
      headlineSuffix: "and sentiment",
      description: "Stop relying on self-reported data. Get real-time insights into every conversation, identify coaching opportunities, and forecast with confidence.",
      points: [
        "Real-time call activity dashboard",
        "Sentiment analysis across all conversations",
        "Identify top performers and replicate success",
        "Spot at-risk deals before they go cold",
      ],
      dashboard: {
        title: "Team Performance",
        subtitle: "Last 30 days",
        calls: "calls",
        pipeline: "Pipeline",
      },
    },
    cta: {
      headline: "Ready to transform your sales team?",
      description: "Join 50+ Israeli companies already saving 8+ hours per rep, every week.",
      placeholder: "Enter your work email",
      button: "Request Pilot",
      submitting: "Submitting...",
      success: "Thanks! We'll be in touch within 24 hours.",
      disclaimer: "No credit card required • 14-day free pilot • Cancel anytime",
    },
    footer: {
      privacy: "Privacy",
      terms: "Terms",
      contact: "Contact",
      copyright: "© 2025 SalesEcho AI. All rights reserved.",
    },
  },
  he: {
    nav: {
      problem: "הבעיה",
      solution: "הפתרון",
      managers: "למנהלים",
      login: "התחברות",
      cta: "בקשת פיילוט",
    },
    hero: {
      badge: "פלטפורמת מכירות ברמה ארגונית",
      headline: "הפוך כל שיחת מכירה ל",
      headlineHighlight: "הזדמנות לצמיחה",
      subheadline: "תובנות אוטומטיות, סנכרון CRM וסיכומים בוואטסאפ –",
      subheadlineHighlight: "אפס הקלדה ידנית.",
      ctaPrimary: "בקשת פיילוט",
      ctaSecondary: "צפה בדמו",
      socialProof: "מהימן על ידי 50+ צוותי מכירות בישראל",
    },
    problem: {
      badge: "הבעיה",
      headline: "נציגי המכירות שלך מבזבזים",
      headlineHighlight: "20% מהיום",
      headlineSuffix: "על עדכוני CRM ידניים",
      description: "כל שיחה מסתיימת באותה שגרה מייגעת: הקלדת הערות, עדכון שדות, תיעוד מעקב. בינתיים, תובנות קריטיות נשכחות ועסקאות מתקררות.",
      points: [
        "8+ שעות בשבוע אובדות להקלדה ידנית",
        "התנגדויות ומחויבויות מפתח נשכחות",
        "נתוני CRM לא עקביים בצוות",
        "מנהלים עיוורים ללא נראות לשיחות",
      ],
      stat: "מזמן המכירה אובד",
      items: [
        { label: "רישום הערות ידני", value: "45 דק׳/יום" },
        { label: "עדכון שדות CRM", value: "30 דק׳/יום" },
        { label: "תזמון מעקב", value: "20 דק׳/יום" },
      ],
    },
    solution: {
      badge: "הפתרון",
      headline: "משיחה ל-CRM ב",
      headlineHighlight: "60 שניות",
      description: "צינור ה-AI שלנו עושה את העבודה הקשה כדי שהנציגים שלך יתמקדו במה שחשוב: סגירת עסקאות.",
      steps: [
        {
          step: "01",
          title: "הקלט",
          description: "העלה או תעד אוטומטית שיחות מכירה מכל מקור. תמיכה בעברית ואנגלית.",
        },
        {
          step: "02",
          title: "נתח",
          description: "AI מחלץ משימות, ערכי עסקה, התנגדויות וצעדים הבאים באופן מיידי.",
        },
        {
          step: "03",
          title: "סנכרן",
          description: "סנכרון בלחיצה ל-HubSpot, Priority, או שיתוף בוואטסאפ. אפס הקלדה.",
        },
      ],
      features: [
        { title: "סיכומי וואטסאפ", desc: "שתף תובנות בלחיצה" },
        { title: "אבטחה ארגונית", desc: "תאימות SOC 2, RLS מופעל" },
        { title: "ניקוד חום עסקה", desc: "דירוג הזדמנויות מונע AI" },
        { title: "מותאם לעברית", desc: "תמיכה מקורית בעברית-אנגלית" },
      ],
    },
    managers: {
      badge: "למנהלים",
      headline: "נראות מלאה אל",
      headlineHighlight: "ביצועי הצוות",
      headlineSuffix: "והסנטימנט",
      description: "הפסק להסתמך על נתונים מדווחים עצמאית. קבל תובנות בזמן אמת על כל שיחה, זהה הזדמנויות לאימון וחזה בביטחון.",
      points: [
        "דשבורד פעילות שיחות בזמן אמת",
        "ניתוח סנטימנט על פני כל השיחות",
        "זהה מצטיינים ושכפל הצלחה",
        "אתר עסקאות בסיכון לפני שהן מתקררות",
      ],
      dashboard: {
        title: "ביצועי צוות",
        subtitle: "30 ימים אחרונים",
        calls: "שיחות",
        pipeline: "צבר",
      },
    },
    cta: {
      headline: "מוכנים להפוך את צוות המכירות שלכם?",
      description: "הצטרפו ל-50+ חברות ישראליות שכבר חוסכות 8+ שעות לנציג, כל שבוע.",
      placeholder: "הזן את אימייל העבודה שלך",
      button: "בקשת פיילוט",
      submitting: "שולח...",
      success: "תודה! ניצור איתך קשר תוך 24 שעות.",
      disclaimer: "ללא כרטיס אשראי • פיילוט חינם ל-14 יום • בטל בכל עת",
    },
    footer: {
      privacy: "פרטיות",
      terms: "תנאים",
      contact: "צור קשר",
      copyright: "© 2025 SalesEcho AI. כל הזכויות שמורות.",
    },
  },
};

type Language = "en" | "he";

export default function LandingPage() {
  const [lang, setLang] = useState<Language>("en");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const t = content[lang];
  const isRTL = lang === "he";
  const ArrowIcon = isRTL ? ArrowLeft : ArrowRight;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    setSubmitted(true);
  };

  const toggleLang = () => {
    setLang(lang === "en" ? "he" : "en");
  };

  return (
    <div
      className="min-h-screen bg-[#0a0f1a] text-white overflow-hidden"
      dir={isRTL ? "rtl" : "ltr"}
    >
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0f1a] via-[#111827] to-[#0a0f1a]" />
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/5 rounded-full blur-[150px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-50 border-b border-white/5 backdrop-blur-xl bg-[#0a0f1a]/80">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">
                SalesEcho<span className="text-cyan-400">.ai</span>
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#problem" className="text-sm text-gray-400 hover:text-white transition-colors">
                {t.nav.problem}
              </a>
              <a href="#solution" className="text-sm text-gray-400 hover:text-white transition-colors">
                {t.nav.solution}
              </a>
              <a href="#managers" className="text-sm text-gray-400 hover:text-white transition-colors">
                {t.nav.managers}
              </a>
              <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                {t.nav.login}
              </Link>
              
              {/* Language Toggle */}
              <button
                onClick={toggleLang}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-sm"
              >
                <Globe className="w-4 h-4" />
                <span>{lang === "en" ? "עב" : "EN"}</span>
              </button>

              <a
                href="#pilot"
                className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-full text-sm font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300"
              >
                {t.nav.cta}
              </a>
            </div>

            {/* Mobile Language Toggle */}
            <div className="flex md:hidden items-center gap-2">
              <button
                onClick={toggleLang}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-sm"
              >
                <Globe className="w-4 h-4" />
                <span>{lang === "en" ? "עב" : "EN"}</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-sm text-gray-300">{t.hero.badge}</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
              {t.hero.headline}{" "}
              <span className="relative inline-block">
                <span className="relative z-10 bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                  {t.hero.headlineHighlight}
                </span>
                <span className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 to-cyan-500/20 blur-2xl" />
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              {t.hero.subheadline}{" "}
              <span className="text-white font-medium">{t.hero.subheadlineHighlight}</span>
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <a
                href="#pilot"
                className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-full text-lg font-semibold hover:shadow-xl hover:shadow-blue-500/30 transition-all duration-300 hover:scale-105"
              >
                {t.hero.ctaPrimary}
                <ArrowIcon className="w-5 h-5 group-hover:translate-x-1 rtl:group-hover:-translate-x-1 transition-transform" />
              </a>
              <button className="flex items-center gap-2 px-8 py-4 bg-white/5 border border-white/10 rounded-full text-lg font-medium hover:bg-white/10 transition-all duration-300">
                <Play className="w-5 h-5" />
                {t.hero.ctaSecondary}
              </button>
            </div>

            {/* Social Proof */}
            <div className="flex flex-col items-center gap-4">
              <div className="flex -space-x-3 rtl:space-x-reverse">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 border-2 border-[#0a0f1a] flex items-center justify-center text-xs font-medium"
                  >
                    {String.fromCharCode(64 + i)}
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
                <span className="text-sm text-gray-400 ms-2">{t.hero.socialProof}</span>
              </div>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="relative mt-20 max-w-5xl mx-auto">
            <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f1a] via-transparent to-transparent z-10" />
            <div className="relative rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-transparent p-1 backdrop-blur-sm">
              <div className="rounded-xl bg-[#111827] p-6 overflow-hidden">
                {/* Mock Dashboard Preview */}
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <div className="flex-1 h-6 rounded bg-white/5" />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2 space-y-4">
                    <div className="h-32 rounded-lg bg-gradient-to-br from-blue-600/20 to-cyan-500/10 border border-blue-500/20 p-4">
                      <div className="text-sm text-blue-400 mb-2">
                        {lang === "en" ? "Latest Call Summary" : "סיכום שיחה אחרון"}
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 w-3/4 rounded bg-white/10" />
                        <div className="h-3 w-1/2 rounded bg-white/10" />
                        <div className="h-3 w-2/3 rounded bg-white/10" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="h-24 rounded-lg bg-white/5 border border-white/10 p-4">
                        <div className="text-xs text-gray-500 mb-1">
                          {lang === "en" ? "Action Items" : "משימות"}
                        </div>
                        <div className="text-2xl font-bold text-emerald-400">12</div>
                      </div>
                      <div className="h-24 rounded-lg bg-white/5 border border-white/10 p-4">
                        <div className="text-xs text-gray-500 mb-1">
                          {lang === "en" ? "Deal Heat" : "חום עסקה"}
                        </div>
                        <div className="text-2xl font-bold text-orange-400">
                          {lang === "en" ? "Hot" : "חם"} 🔥
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="h-20 rounded-lg bg-white/5 border border-white/10" />
                    <div className="h-20 rounded-lg bg-white/5 border border-white/10" />
                    <div className="h-20 rounded-lg bg-white/5 border border-white/10" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* The Problem Section */}
      <section id="problem" className="relative z-10 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 mb-6">
                <Clock className="w-4 h-4 text-red-400" />
                <span className="text-sm text-red-400">{t.problem.badge}</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                {t.problem.headline}{" "}
                <span className="text-red-400">{t.problem.headlineHighlight}</span>{" "}
                {t.problem.headlineSuffix}
              </h2>
              <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                {t.problem.description}
              </p>
              <ul className="space-y-4">
                {t.problem.points.map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="mt-1 w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                    </div>
                    <span className="text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-red-600/10 to-orange-500/10 rounded-3xl blur-3xl" />
              <div className="relative bg-gradient-to-br from-[#1a1f2e] to-[#111827] rounded-2xl border border-white/10 p-8">
                <div className="text-center mb-8">
                  <div className="text-7xl font-bold text-red-400 mb-2">20%</div>
                  <div className="text-gray-400">{t.problem.stat}</div>
                </div>
                <div className="space-y-4">
                  {t.problem.items.map((item, i) => (
                    <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                      <span className="text-gray-400">{item.label}</span>
                      <span className="text-red-400 font-semibold">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* The Solution Section */}
      <section id="solution" className="relative z-10 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
              <Zap className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400">{t.solution.badge}</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              {t.solution.headline}{" "}
              <span className="text-emerald-400">{t.solution.headlineHighlight}</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              {t.solution.description}
            </p>
          </div>

          {/* Pipeline Steps */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {t.solution.steps.map((item, i) => {
              const icons = [Mic, Brain, RefreshCw];
              const colors = ["blue", "purple", "emerald"];
              const Icon = icons[i];
              const color = colors[i];

              return (
                <div key={i} className="group relative">
                  {/* Connector Line */}
                  {i < 2 && (
                    <div className={`hidden md:block absolute top-1/2 ${isRTL ? '-left-4' : '-right-4'} w-8 h-0.5 bg-gradient-to-r from-white/20 to-transparent`} />
                  )}
                  <div className="relative h-full rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-transparent p-8 hover:border-white/20 transition-all duration-300 group-hover:translate-y-[-4px]">
                    <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-${color}-500/10 border border-${color}-500/20 mb-6`}>
                      <Icon className={`w-7 h-7 text-${color}-400`} />
                    </div>
                    <div className="text-sm text-gray-500 mb-2">
                      {lang === "en" ? "Step" : "שלב"} {item.step}
                    </div>
                    <h3 className="text-2xl font-bold mb-3">{item.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{item.description}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {t.solution.features.map((feature, i) => {
              const icons = [MessageSquare, Shield, TrendingUp, CheckCircle];
              const Icon = icons[i];

              return (
                <div
                  key={i}
                  className="flex items-start gap-4 p-6 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <div className="font-semibold mb-1">{feature.title}</div>
                    <div className="text-sm text-gray-500">{feature.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* For Managers Section */}
      <section id="managers" className="relative z-10 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className={isRTL ? "order-1" : "order-2 lg:order-1"}>
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/10 to-purple-500/10 rounded-3xl blur-3xl" />
                <div className="relative bg-gradient-to-br from-[#1a1f2e] to-[#111827] rounded-2xl border border-white/10 p-8">
                  {/* Manager Dashboard Mock */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <Users className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="font-semibold">{t.managers.dashboard.title}</div>
                      <div className="text-sm text-gray-500">{t.managers.dashboard.subtitle}</div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    {[
                      { name: "Yossi K.", calls: 47, deals: "₪450K", heat: 92 },
                      { name: "Dana L.", calls: 38, deals: "₪320K", heat: 85 },
                      { name: "Amit R.", calls: 52, deals: "₪280K", heat: 78 },
                    ].map((rep, i) => (
                      <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-white/5">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center text-sm font-medium">
                          {rep.name.split(" ").map((n) => n[0]).join("")}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium">{rep.name}</div>
                          <div className="text-sm text-gray-500">
                            {rep.calls} {t.managers.dashboard.calls}
                          </div>
                        </div>
                        <div className={`text-${isRTL ? 'left' : 'right'}`}>
                          <div className="font-semibold text-emerald-400">{rep.deals}</div>
                          <div className="text-xs text-gray-500">{t.managers.dashboard.pipeline}</div>
                        </div>
                        <div className="w-16">
                          <div className={`text-${isRTL ? 'left' : 'right'} text-sm text-gray-400 mb-1`}>{rep.heat}%</div>
                          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                              style={{ width: `${rep.heat}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className={isRTL ? "order-2" : "order-1 lg:order-2"}>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-6">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <span className="text-sm text-indigo-400">{t.managers.badge}</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                {t.managers.headline}{" "}
                <span className="text-indigo-400">{t.managers.headlineHighlight}</span>{" "}
                {t.managers.headlineSuffix}
              </h2>
              <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                {t.managers.description}
              </p>
              <ul className="space-y-4">
                {t.managers.points.map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="pilot" className="relative z-10 py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-3xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-cyan-500" />
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIgMS44LTQgNC00czQgMS44IDQgNC0xLjggNC00IDQtNC0xLjgtNC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
            <div className="relative px-8 py-16 md:px-16 md:py-20 text-center">
              <h2 className="text-3xl md:text-5xl font-bold mb-4">
                {t.cta.headline}
              </h2>
              <p className="text-lg md:text-xl text-white/80 mb-10 max-w-xl mx-auto">
                {t.cta.description}
              </p>
              {!submitted ? (
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
                  <input
                    type="email"
                    placeholder={t.cta.placeholder}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="flex-1 px-6 py-4 rounded-full bg-white/10 border border-white/20 placeholder-white/50 text-white focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                    required
                    dir="ltr"
                  />
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-8 py-4 bg-white text-blue-600 rounded-full font-semibold hover:bg-white/90 transition-colors disabled:opacity-70 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
                        {t.cta.submitting}
                      </>
                    ) : (
                      <>
                        {t.cta.button}
                        <ArrowIcon className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <div className="flex items-center justify-center gap-3 text-lg">
                  <CheckCircle className="w-6 h-6" />
                  <span>{t.cta.success}</span>
                </div>
              )}
              <p className="text-sm text-white/60 mt-6">
                {t.cta.disclaimer}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold">SalesEcho.ai</span>
            </div>
            <div className="flex items-center gap-8 text-sm text-gray-500">
              <a href="#" className="hover:text-white transition-colors">{t.footer.privacy}</a>
              <a href="#" className="hover:text-white transition-colors">{t.footer.terms}</a>
              <a href="#" className="hover:text-white transition-colors">{t.footer.contact}</a>
            </div>
            <div className="text-sm text-gray-500">
              {t.footer.copyright}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
