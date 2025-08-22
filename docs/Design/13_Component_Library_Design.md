# docs\Design\13_Component_Library_Design.md
# 🧩 Component Library Design - Day 9
## Basic Components & Data Visualization Elements

---

## 🧩 **Basic Components (صبح - 4 ساعت)**

### **🔘 Buttons: Primary, Secondary, Tertiary Variants (1 ساعت)**

#### **🎯 Button Design Philosophy**
```
BUTTON DESIGN SYSTEM PRINCIPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 VISUAL HIERARCHY STRATEGY:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Primary Buttons: High emphasis actions                                      │
│ ├── Execute trades, confirm transactions, save critical data                │
│ ├── Maximum visual weight with filled background                            │
│ ├── CryptoBlue-500 background with white text                              │
│ └── Used sparingly - only 1 primary per screen section                     │
│                                                                             │
│ Secondary Buttons: Medium emphasis actions                                  │
│ ├── View details, open modals, navigate to sections                        │
│ ├── Medium visual weight with border and background                        │
│ ├── Light background with primary text color                               │
│ └── Support primary actions without competing                              │
│                                                                             │
│ Tertiary Buttons: Low emphasis actions                                     │
│ ├── Cancel, close, dismiss, secondary navigation                           │
│ ├── Minimal visual weight - text or icon only                              │
│ ├── No background, minimal styling                                         │
│ └── Accessible but unobtrusive                                             │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 FUNCTIONAL CATEGORIZATION:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Action Type        │ Visual Style    │ Usage Context                        │
├────────────────────┼─────────────────┼──────────────────────────────────────┤
│ 💰 Financial       │ Primary Solid   │ Execute Signal, Buy/Sell, Confirm   │
│ Actions            │ High Impact     │ Transfer, Withdraw, Deposit          │
├────────────────────┼─────────────────┼──────────────────────────────────────┤
│ 📊 Data Actions    │ Secondary       │ View Chart, Analyze, Export Data    │
│                    │ Outlined        │ Filter, Sort, Refresh               │
├────────────────────┼─────────────────┼──────────────────────────────────────┤
│ 🧭 Navigation      │ Tertiary        │ Back, Next, Close, Cancel          │
│ Actions            │ Text/Ghost      │ Navigate Between Pages               │
├────────────────────┼─────────────────┼──────────────────────────────────────┤
│ ⚠️ Destructive     │ Danger Primary  │ Delete, Remove, Stop Loss           │
│ Actions            │ Red Background  │ Clear Data, Reset Settings          │
├────────────────────┼─────────────────┼──────────────────────────────────────┤
│ 🤖 AI Actions      │ Special Accent  │ Ask AI, Get Explanation, Auto-Opt   │
│                    │ Purple Gradient │ Smart Suggestion, AI Analysis       │
└────────────────────┴─────────────────┴──────────────────────────────────────┘
```

#### **🔘 Primary Button Specifications**
```
PRIMARY BUTTON COMPONENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 VISUAL SPECIFICATIONS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        Execute Signal                                   │ │
│ │ Background: #0B8AFF (CryptoBlue-500)                                   │ │
│ │ Text: #FFFFFF (White)                                                   │ │
│ │ Border: None                                                            │ │
│ │ Border Radius: 8px                                                      │ │
│ │ Padding: 12px 24px (Medium), 16px 32px (Large)                         │ │
│ │ Font: Inter Medium (500), 14px/16px (Med), 16px/18px (Large)           │ │
│ │ Box Shadow: 0 1px 2px rgba(0, 0, 0, 0.05)                              │ │
│ │ Transition: all 150ms ease-in-out                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Hover State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        Execute Signal                                   │ │
│ │ Background: #0066CC (CryptoBlue-600)                                   │ │
│ │ Text: #FFFFFF (White)                                                   │ │
│ │ Transform: translateY(-1px)                                             │ │
│ │ Box Shadow: 0 4px 8px rgba(11, 138, 255, 0.25)                         │ │
│ │ Cursor: pointer                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Active/Pressed State:                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        Execute Signal                                   │ │
│ │ Background: #004C99 (CryptoBlue-700)                                   │ │
│ │ Text: #FFFFFF (White)                                                   │ │
│ │ Transform: translateY(0px)                                              │ │
│ │ Box Shadow: 0 1px 2px rgba(0, 0, 0, 0.1)                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Disabled State:                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                        Execute Signal                                   │ │
│ │ Background: #F1F5F9 (NightSlate-100)                                   │ │
│ │ Text: #94A3B8 (NightSlate-400)                                         │ │
│ │ Cursor: not-allowed                                                     │ │
│ │ Opacity: 0.6                                                            │ │
│ │ Box Shadow: none                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Loading State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                    ⟳ Processing...                                      │ │
│ │ Background: #0B8AFF (CryptoBlue-500)                                   │ │
│ │ Text: #FFFFFF with spinner icon                                         │ │
│ │ Pointer Events: none                                                    │ │
│ │ Spinner: 16px rotating icon, 1s animation                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

📐 SIZE VARIANTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Small Primary: Height 32px, Padding 8px 16px, Font 12px/14px               │
│ ├── Usage: Table actions, compact interfaces, mobile secondary actions     │
│ ├── Min Width: 64px, Max Width: 120px                                      │
│ └── Icon Size: 12px with 4px margin                                        │
│                                                                             │
│ Medium Primary: Height 40px, Padding 12px 24px, Font 14px/16px             │
│ ├── Usage: Standard forms, modal actions, desktop primary buttons          │
│ ├── Min Width: 80px, Max Width: 200px                                      │
│ └── Icon Size: 16px with 8px margin                                        │
│                                                                             │
│ Large Primary: Height 48px, Padding 16px 32px, Font 16px/18px              │
│ ├── Usage: Hero CTAs, major actions, mobile primary buttons                │
│ ├── Min Width: 120px, Max Width: 280px                                     │
│ └── Icon Size: 20px with 8px margin                                        │
│                                                                             │
│ Extra Large: Height 56px, Padding 20px 40px, Font 18px/20px                │
│ ├── Usage: Landing page CTAs, major conversions, hero sections             │
│ ├── Min Width: 160px, Max Width: 320px                                     │
│ └── Icon Size: 24px with 12px margin                                       │
└─────────────────────────────────────────────────────────────────────────────┘

🎨 SPECIALIZED PRIMARY VARIANTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Success Primary (Profit Actions):                                          │
│ ├── Background: #22C55E (ProfitGreen-500)                                  │
│ ├── Hover: #16A34A (ProfitGreen-600)                                       │
│ ├── Usage: Execute Long, Take Profit, Confirm Gains                        │
│ └── Icon: ↗️ trending up, ✅ check mark                                    │
│                                                                             │
│ Danger Primary (Risk Actions):                                             │
│ ├── Background: #EF4444 (LossRed-500)                                      │
│ ├── Hover: #DC2626 (LossRed-600)                                           │
│ ├── Usage: Execute Short, Stop Loss, Delete Portfolio                      │
│ └── Icon: ↘️ trending down, ⚠️ warning, 🗑️ delete                        │
│                                                                             │
│ AI Primary (Smart Actions):                                                │
│ ├── Background: linear-gradient(135deg, #0B8AFF 0%, #A855F7 100%)          │
│ ├── Hover: Enhanced gradient with brightness increase                      │
│ ├── Usage: Ask AI, Get Recommendations, Auto-Optimize                      │
│ └── Icon: 🤖 robot, 🧠 brain, ⚡ lightning                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **🔘 Secondary Button Specifications**
```
SECONDARY BUTTON COMPONENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 VISUAL SPECIFICATIONS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                         View Details                                    │ │
│ │ Background: #FFFFFF (White)                                             │ │
│ │ Text: #0B8AFF (CryptoBlue-500)                                         │ │
│ │ Border: 1px solid #E2E8F0 (NightSlate-200)                             │ │
│ │ Border Radius: 8px                                                      │ │
│ │ Padding: 12px 24px (Medium), 16px 32px (Large)                         │ │
│ │ Font: Inter Medium (500), 14px/16px (Med), 16px/18px (Large)           │ │
│ │ Box Shadow: none                                                        │ │
│ │ Transition: all 150ms ease-in-out                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Hover State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                         View Details                                    │ │
│ │ Background: #F8FAFC (NightSlate-50)                                    │ │
│ │ Text: #0066CC (CryptoBlue-600)                                         │ │
│ │ Border: 1px solid #0B8AFF (CryptoBlue-500)                             │ │
│ │ Transform: translateY(-1px)                                             │ │
│ │ Box Shadow: 0 2px 4px rgba(11, 138, 255, 0.1)                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Active/Pressed State:                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                         View Details                                    │ │
│ │ Background: #E0F0FF (CryptoBlue-100)                                   │ │
│ │ Text: #004C99 (CryptoBlue-700)                                         │ │
│ │ Border: 1px solid #0066CC (CryptoBlue-600)                             │ │
│ │ Transform: translateY(0px)                                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Disabled State:                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                         View Details                                    │ │
│ │ Background: #FFFFFF (White)                                             │ │
│ │ Text: #94A3B8 (NightSlate-400)                                         │ │
│ │ Border: 1px solid #F1F5F9 (NightSlate-100)                             │ │
│ │ Cursor: not-allowed                                                     │ │
│ │ Opacity: 0.6                                                            │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

🌙 DARK MODE SPECIFICATIONS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default Dark:                                                               │
│ ├── Background: #334155 (NightSlate-700)                                   │
│ ├── Text: #42A8FF (CryptoBlue-400)                                         │
│ ├── Border: 1px solid #475569 (NightSlate-600)                             │
│                                                                             │
│ Hover Dark:                                                                 │
│ ├── Background: #475569 (NightSlate-600)                                   │
│ ├── Text: #7CC4FF (CryptoBlue-300)                                         │
│ ├── Border: 1px solid #42A8FF (CryptoBlue-400)                             │
│                                                                             │
│ Active Dark:                                                                │
│ ├── Background: #1E293B (NightSlate-800)                                   │
│ ├── Text: #0B8AFF (CryptoBlue-500)                                         │
│ ├── Border: 1px solid #7CC4FF (CryptoBlue-300)                             │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 SECONDARY VARIANTS BY FUNCTION:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Info Secondary:                                                             │
│ ├── Text: #A855F7 (TechPurple-500), Border: TechPurple-200                │
│ ├── Usage: Learn More, Get Help, View Tutorial                             │
│ └── Icon: ℹ️ info, 📚 book, 🎓 graduation                                │
│                                                                             │
│ Warning Secondary:                                                          │
│ ├── Text: #F59E0B (CautionAmber-500), Border: CautionAmber-200            │
│ ├── Usage: Review Required, Attention Needed, Moderate Risk                │
│ └── Icon: ⚠️ warning, 👁️ eye, ⏰ clock                                   │
│                                                                             │
│ Success Secondary:                                                          │
│ ├── Text: #22C55E (ProfitGreen-500), Border: ProfitGreen-200              │
│ ├── Usage: View Gains, Check Performance, See Results                      │
│ └── Icon: ✅ check, 📈 trending up, 🎯 target                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **🔘 Tertiary Button Specifications**
```
TERTIARY BUTTON COMPONENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 GHOST BUTTON (Text Only):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                           Cancel                                        │ │
│ │ Background: Transparent                                                 │ │
│ │ Text: #64748B (NightSlate-500)                                         │ │
│ │ Border: none                                                            │ │
│ │ Padding: 12px 16px (Medium), 16px 20px (Large)                         │ │
│ │ Font: Inter Regular (400), 14px/16px (Med), 16px/18px (Large)          │ │
│ │ Underline: none                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Hover State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                           Cancel                                        │ │
│ │ Background: rgba(100, 116, 139, 0.1)                                   │ │
│ │ Text: #334155 (NightSlate-700)                                         │ │
│ │ Border Radius: 6px                                                      │ │
│ │ Underline: none                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Active State:                                                               │
│ ├── Background: rgba(100, 116, 139, 0.2)                                   │
│ ├── Text: #1E293B (NightSlate-800)                                         │
│ └── Transform: none (no movement for tertiary)                             │
└─────────────────────────────────────────────────────────────────────────────┘

🔗 LINK BUTTON (Underlined Text):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                      Learn More →                                       │ │
│ │ Background: Transparent                                                 │ │
│ │ Text: #0B8AFF (CryptoBlue-500)                                         │ │
│ │ Text Decoration: underline                                              │ │
│ │ Underline Color: transparent                                            │ │
│ │ Padding: 4px 8px (minimal)                                              │ │
│ │ Font: Inter Regular (400), inherit parent size                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Hover State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                      Learn More →                                       │ │
│ │ Text: #0066CC (CryptoBlue-600)                                         │ │
│ │ Underline Color: #0066CC (CryptoBlue-600)                              │ │
│ │ Underline Offset: 2px                                                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Active State:                                                               │
│ ├── Text: #004C99 (CryptoBlue-700)                                         │
│ ├── Underline Color: #004C99 (CryptoBlue-700)                              │
│ └── Underline Thickness: 2px                                               │
└─────────────────────────────────────────────────────────────────────────────┘

📱 ICON BUTTON (Icon Only):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Size Variants:                                                              │
│ ├── Small: 32px × 32px (Icon 16px)                                         │
│ ├── Medium: 40px × 40px (Icon 20px)                                        │
│ ├── Large: 48px × 48px (Icon 24px)                                         │
│ └── XL: 56px × 56px (Icon 28px)                                            │
│                                                                             │
│ Default State:                                                              │
│ ├── Background: Transparent                                                 │
│ ├── Icon Color: #64748B (NightSlate-500)                                   │
│ ├── Border Radius: 6px                                                     │
│ ├── Padding: 8px (all variants maintain proportion)                        │
│                                                                             │
│ Hover State:                                                                │
│ ├── Background: rgba(100, 116, 139, 0.1)                                   │
│ ├── Icon Color: #334155 (NightSlate-700)                                   │
│ ├── Transform: scale(1.05)                                                 │
│                                                                             │
│ Active State:                                                               │
│ ├── Background: rgba(100, 116, 139, 0.2)                                   │
│ ├── Icon Color: #1E293B (NightSlate-800)                                   │
│ ├── Transform: scale(1.0)                                                  │
│                                                                             │
│ Common Icons:                                                               │
│ ├── ⚙️ Settings, 📊 Analytics, ℹ️ Info, ❌ Close                          │
│ ├── 📤 Share, 💾 Save, 🔄 Refresh, 🔍 Search                             │
│ ├── ➕ Add, ➖ Remove, ✏️ Edit, 🗑️ Delete                                 │
│ └── ← → ↑ ↓ Directional navigation                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **📝 Form Elements: Inputs, Selects, Checkboxes (1.5 ساعت)**

#### **📋 Input Field Specifications**
```
INPUT COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 TEXT INPUT (Base Component):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Email Address                                                        │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Enter your email address                                            │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Label: Inter Medium (500), 14px, #334155 (NightSlate-700)              │ │
│ │ Input: System UI Regular (400), 16px, #0F172A (NightSlate-900)         │ │
│ │ Placeholder: System UI Regular (400), 16px, #94A3B8 (NightSlate-400)   │ │
│ │ Background: #FFFFFF (White)                                             │ │
│ │ Border: 1px solid #D1D5DB (NightSlate-300)                             │ │
│ │ Border Radius: 8px                                                      │ │
│ │ Padding: 12px 16px                                                      │ │
│ │ Height: 44px (touch-friendly)                                           │ │
│ │ Transition: all 150ms ease-in-out                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Focus State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Email Address                                                        │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ user@example.com|                                                   │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Border: 2px solid #0B8AFF (CryptoBlue-500)                             │ │
│ │ Box Shadow: 0 0 0 3px rgba(11, 138, 255, 0.1)                          │ │
│ │ Outline: none (custom focus ring)                                       │ │
│ │ Background: #FFFFFF (unchanged)                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Error State:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Email Address                                                        │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ invalid-email                                                       │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │ ⚠️ Please enter a valid email address                                   │ │
│ │                                                                         │ │
│ │ Border: 2px solid #EF4444 (LossRed-500)                                │ │
│ │ Error Text: Inter Regular (400), 12px, #B91C1C (LossRed-700)           │ │
│ │ Error Icon: ⚠️ 16px, aligned with text                                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Success State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Email Address                                                        │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ user@example.com                                                    │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │ ✅ Email address is valid                                               │ │
│ │                                                                         │ │
│ │ Border: 2px solid #22C55E (ProfitGreen-500)                            │ │
│ │ Success Text: Inter Regular (400), 12px, #15803D (ProfitGreen-700)     │ │
│ │ Success Icon: ✅ 16px, aligned with text                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Disabled State:                                                             │
│ ├── Background: #F8FAFC (NightSlate-50)                                    │
│ ├── Border: 1px solid #E2E8F0 (NightSlate-200)                             │
│ ├── Text: #94A3B8 (NightSlate-400)                                         │
│ ├── Cursor: not-allowed                                                    │ │
│ └── Opacity: 0.6                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

💰 FINANCIAL INPUT VARIANTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Currency Input:                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Investment Amount                                                    │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ $ │ 1,250.00                                                        │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Prefix: $ symbol, non-editable, #64748B (NightSlate-500)               │ │
│ │ Format: Auto-format with commas, 2 decimal places                      │ │
│ │ Font: JetBrains Mono Regular (400) for consistent number spacing       │ │
│ │ Min/Max: Validation for reasonable financial amounts                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Percentage Input:                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Portfolio Allocation                                                 │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 25.5 │ %                                                             │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Suffix: % symbol, non-editable, #64748B (NightSlate-500)               │ │
│ │ Range: 0-100 with step validation                                      │ │
│ │ Format: 1 decimal place, auto-round                                    │ │
│ │ Visual: Progress bar below showing percentage                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Crypto Address Input:                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Wallet Address                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa                    │ 📋 │ 🔍 │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Font: JetBrains Mono Regular (400) for character clarity               │ │
│ │ Actions: Copy button, QR scanner, validation                           │ │
│ │ Validation: Real-time format checking                                  │ │
│ │ Security: Hide middle characters (1A1z...DivfNa)                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **📋 Select & Dropdown Specifications**
```
SELECT COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 SINGLE SELECT (Dropdown):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Closed State:                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Select Cryptocurrency                                                │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟡 Bitcoin (BTC)                                           ᐯ       │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Background: #FFFFFF (White)                                             │ │
│ │ Border: 1px solid #D1D5DB (NightSlate-300)                             │ │
│ │ Border Radius: 8px                                                      │ │
│ │ Padding: 12px 16px                                                      │ │
│ │ Height: 44px                                                            │ │
│ │ Icon: Chevron down ᐯ, 20px, #64748B (NightSlate-500)                   │ │
│ │ Text: Selected option with icon, #0F172A (NightSlate-900)              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Open State:                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Select Cryptocurrency                                                │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟡 Bitcoin (BTC)                                           ᐱ       │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟡 Bitcoin (BTC)                                       ✓           │ │ │
│ │ │ 🔷 Ethereum (ETH)                                                   │ │ │
│ │ │ 🔵 Binance Coin (BNB)                                              │ │ │
│ │ │ ⚪ Cardano (ADA)                                                    │ │ │
│ │ │ 🟣 Solana (SOL)                                                     │ │ │
│ │ │ ────────────────────────────────                                   │ │ │
│ │ │ 💰 View All 50+ Coins                                              │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Dropdown: White background, border, shadow                             │ │
│ │ Options: Hover bg #F8FAFC, selected bg #E0F0FF                         │ │
│ │ Max Height: 200px with scroll                                          │ │
│ │ Position: Below input, auto-flip if space limited                      │ │
│ │ Search: Built-in filter for long lists                                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Searchable Variant:                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Search & Select Cryptocurrency                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🔍 Search or select...                                     ᐯ       │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Features:                                                               │ │
│ ├── Type to search through options                                       │ │
│ ├── Keyboard navigation (↑↓ arrow keys)                                  │ │
│ ├── Clear selection with X button                                        │ │
│ ├── Recent selections shown first                                        │ │
│ └── Auto-complete and fuzzy matching                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 MULTI-SELECT (Tag Input):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Multi-Select with Tags:                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Select Portfolio Assets                                              │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟡 Bitcoin ✕  🔷 Ethereum ✕  🔵 BNB ✕  🔍 Add more...          │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ Selected Tags:                                                          │ │
│ ├── Background: #E0F0FF (CryptoBlue-100)                                   │ │
│ ├── Text: #004C99 (CryptoBlue-700)                                         │ │
│ ├── Remove: ✕ button, hover shows #EF4444 (LossRed-500)                   │ │
│ ├── Spacing: 4px gap between tags                                          │ │
│ └── Max Width: Truncate long names with tooltip                            │ │
│                                                                             │ │
│ Input Area:                                                                 │ │
│ ├── Placeholder: "Add more..." when tags present                           │ │
│ ├── Auto-expand: Height grows with tag count                               │ │
│ ├── Keyboard: Delete removes last tag                                      │ │
│ ├── Limit: Visual indicator when max reached                               │ │
│ └── Validation: Duplicate prevention                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **☑️ Checkbox & Radio Specifications**
```
CHECKBOX & RADIO COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☑️ CHECKBOX COMPONENT:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Unchecked State:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ Enable real-time notifications                                       │ │
│ │                                                                         │ │
│ │ Checkbox: 20px × 20px                                                   │ │
│ │ Background: #FFFFFF (White)                                             │ │
│ │ Border: 2px solid #D1D5DB (NightSlate-300)                             │ │
│ │ Border Radius: 4px                                                      │ │
│ │ Label: Inter Regular (400), 16px, #334155 (NightSlate-700)             │ │
│ │ Spacing: 12px between checkbox and label                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Checked State:                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☑️ Enable real-time notifications                                       │ │
│ │                                                                         │ │
│ │ Background: #0B8AFF (CryptoBlue-500)                                   │ │
│ │ Border: 2px solid #0B8AFF (CryptoBlue-500)                             │ │
│ │ Checkmark: ✓ white, 14px, centered                                     │ │
│ │ Animation: Smooth fade-in 150ms                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Indeterminate State:                                                        │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ Select all assets (2 of 5 selected)                                  │ │
│ │                                                                         │ │
│ │ Background: #0B8AFF (CryptoBlue-500)                                   │ │
│ │ Symbol: – (dash) white, 12px, centered                                 │ │
│ │ Usage: Parent checkboxes with partial child selection                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Hover State:                                                                │
│ ├── Border: 2px solid #42A8FF (CryptoBlue-400)                             │
│ ├── Background: #F8FAFC (NightSlate-50) if unchecked                       │
│ ├── Cursor: pointer                                                        │
│ └── Transform: scale(1.05)                                                 │
│                                                                             │
│ Focus State:                                                                │
│ ├── Outline: 2px solid #0B8AFF (CryptoBlue-500) with 2px offset           │ │
│ ├── Outline Offset: 2px                                                    │ │
│ └── Visible focus ring for keyboard navigation                             │ │
│                                                                             │
│ Disabled State:                                                             │
│ ├── Background: #F8FAFC (NightSlate-50)                                    │ │
│ ├── Border: 2px solid #E2E8F0 (NightSlate-200)                             │ │
│ ├── Label: #94A3B8 (NightSlate-400)                                        │ │
│ ├── Cursor: not-allowed                                                    │ │
│ └── Opacity: 0.6                                                           │ │
└─────────────────────────────────────────────────────────────────────────────┘

🔘 RADIO BUTTON COMPONENT:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Radio Group Example:                                                        │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏷️ Investment Strategy                                                  │ │
│ │                                                                         │ │
│ │ ○ Conservative (Low Risk)                                               │ │
│ │ ● Balanced (Medium Risk)         ← Selected                            │ │
│ │ ○ Aggressive (High Risk)                                                │ │
│ │ ○ Custom Strategy                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Unselected State:                                                           │
│ ├── Circle: 20px diameter                                                  │ │
│ ├── Background: #FFFFFF (White)                                             │ │
│ ├── Border: 2px solid #D1D5DB (NightSlate-300)                             │ │
│ ├── Inner Circle: none                                                     │ │
│                                                                             │
│ Selected State:                                                             │
│ ├── Background: #FFFFFF (White)                                             │ │
│ ├── Border: 2px solid #0B8AFF (CryptoBlue-500)                             │ │
│ ├── Inner Circle: 8px, #0B8AFF (CryptoBlue-500), centered                  │ │
│ ├── Animation: Scale-in 200ms ease-out                                     │ │
│                                                                             │
│ Hover State:                                                                │
│ ├── Border: 2px solid #42A8FF (CryptoBlue-400)                             │ │
│ ├── Background: #F8FAFC (NightSlate-50)                                    │ │
│ ├── Transform: scale(1.05)                                                 │ │
│                                                                             │
│ Label Specifications:                                                       ││
│ ├── Font: Inter Regular (400), 16px                                        │ │
│ ├── Color: #334155 (NightSlate-700)                                        │ │
│ ├── Spacing: 12px from radio button                                        │ │
│ ├── Line Height: 1.5 for multi-line labels                                 │ │
│ ├── Click Area: Entire label clickable                                     │ │
│ └── Hover: Slight color change to indicate interactivity                   │ │
└─────────────────────────────────────────────────────────────────────────────┘

🎚️ TOGGLE SWITCH COMPONENT:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Off State:                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔔 Push Notifications               ○────────                           │ │
│ │                                                                         │ │
│ │ Track: 44px width × 24px height                                         │ │
│ │ Background: #E2E8F0 (NightSlate-200)                                   │ │
│ │ Border Radius: 12px (pill shape)                                       │ │
│ │ Thumb: 20px circle, #FFFFFF, 2px left offset                           │ │
│ │ Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)                                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ On State:                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔔 Push Notifications                       ────────○                   │ │
│ │                                                                         │ │
│ │ Track Background: #22C55E (ProfitGreen-500)                            │ │
│ │ Thumb: 20px circle, #FFFFFF, 22px right offset                         │ │
│ │ Animation: Smooth slide 200ms ease-in-out                              │ │
│ │ Icon: Optional ✓ on track or thumb                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Size Variants:                                                              │
│ ├── Small: 36px × 20px (16px thumb)                                        │ │
│ ├── Medium: 44px × 24px (20px thumb) ← Default                             │ │
│ ├── Large: 52px × 28px (24px thumb)                                        │ │
│                                                                             │
│ Color Variants:                                                             │
│ ├── Success: #22C55E (ProfitGreen-500) - Default on state                  │ │
│ ├── Primary: #0B8AFF (CryptoBlue-500) - Alternative on state               │ │
│ ├── Warning: #F59E0B (CautionAmber-500) - Caution toggles                  │ │
│ └── Danger: #EF4444 (LossRed-500) - Destructive toggles                    │ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **🃏 Cards: Content Cards, Metric Cards (1.5 ساعت)**

#### **📋 Content Card Specifications**
```
CARD COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🃏 BASIC CONTENT CARD:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Default Content Card:                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Market Analysis                                          ⚙️ •••      │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ The current market shows strong bullish momentum with                   │ │
│ │ increased volume and positive sentiment indicators.                     │ │
│ │ AI confidence level is at 87% for continued growth.                     │ │
│ │                                                                         │ │
│ │ 🏷️ Tags: #BullMarket #AI #Analysis                                      │ │
│ │                                                                         │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │ 📅 2 hours ago                                    [🔗 View Details]     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Structure Elements:                                                         │
│ ├── Header: Title + Action Menu (24px height)                              │
│ ├── Divider: 1px solid #E2E8F0 (NightSlate-200)                           │
│ ├── Content: Flexible body area (min 80px height)                          │
│ ├── Tags: Optional tag row (32px height when present)                      │
│ ├── Footer: Metadata + Actions (40px height)                               │
│                                                                             │
│ Visual Specifications:                                                      │
│ ├── Background: #FFFFFF (White)                                             │
│ ├── Border: 1px solid #E2E8F0 (NightSlate-200)                             │
│ ├── Border Radius: 12px                                                    │
│ ├── Padding: 20px (Desktop), 16px (Mobile)                                 │
│ ├── Box Shadow: 0 1px 3px rgba(0, 0, 0, 0.05)                              │
│ ├── Hover Shadow: 0 4px 12px rgba(0, 0, 0, 0.1)                            │
│ └── Transition: all 200ms ease-in-out                                      │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 INTERACTIVE CARD STATES:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Hover State:                                                                │
│ ├── Transform: translateY(-2px)                                             │
│ ├── Box Shadow: 0 8px 24px rgba(0, 0, 0, 0.12)                             │
│ ├── Border: 1px solid #CBD5E1 (NightSlate-300)                             │
│ └── Cursor: pointer (for clickable cards)                                  │
│                                                                             │
│ Active State:                                                               │
│ ├── Transform: translateY(0px)                                              │
│ ├── Box Shadow: 0 2px 8px rgba(0, 0, 0, 0.08)                              │
│ ├── Border: 1px solid #0B8AFF (CryptoBlue-500)                             │
│                                                                             │
│ Loading State:                                                              │
│ ├── Content: Skeleton placeholders                                         │
│ ├── Animation: Subtle shimmer effect                                       │
│ ├── Opacity: 0.7                                                           │
│ └── Pointer Events: none                                                   │
│                                                                             │
│ Error State:                                                                │
│ ├── Border: 1px solid #FEE2E2 (LossRed-100)                                │
│ ├── Background: #FEF2F2 (LossRed-50)                                       │
│ ├── Icon: ⚠️ Error indicator in header                                     │
│ └── Action: "Retry" button in footer                                       │
└─────────────────────────────────────────────────────────────────────────────┘

💰 FINANCIAL METRIC CARD:
┌─────────────────────────────────────────────────────────────────────────────┐
│ KPI Metric Card:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                         Portfolio Value                                 │ │
│ │                                                                         │ │
│ │                        $127,450.82                                     │ │
│ │                         📈 +5.2%                                        │ │
│ │                                                                         │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒                              │ │
│ │                                                                         │ │
│ │ Last updated: 2 minutes ago                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Metric Value:                                                               │
│ ├── Font: Inter SemiBold (600), 32px (Large), 24px (Medium)                │
│ ├── Color: #0F172A (NightSlate-900)                                        │
│ ├── Format: Currency with proper comma separation                          │
│ ├── Alignment: Center                                                      │
│                                                                             │
│ Change Indicator:                                                           │
│ ├── Positive: #22C55E (ProfitGreen-500), ↗️ arrow                          │
│ ├── Negative: #EF4444 (LossRed-500), ↘️ arrow                              │
│ ├── Neutral: #64748B (NightSlate-500), → arrow                             │
│ ├── Font: Inter Medium (500), 18px                                         │
│                                                                             │
│ Progress Bar:                                                               │
│ ├── Height: 4px                                                            │
│ ├── Background: #E2E8F0 (NightSlate-200)                                   │
│ ├── Fill: Gradient based on performance                                    │
│ ├── Animation: Smooth fill animation on load                               │
│                                                                             │
│ Metadata:                                                                   │
│ ├── Font: Inter Regular (400), 12px                                        │
│ ├── Color: #64748B (NightSlate-500)                                        │
│ ├── Position: Bottom center                                                │ │
│ └── Live Indicator: ● green dot for real-time updates                      │ │
└─────────────────────────────────────────────────────────────────────────────┘

🚨 ALERT CARD VARIANTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Success Alert Card:                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ✅ Trade Executed Successfully                              [✕ Dismiss] │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ Your BTC long position has been executed at $43,210.                   │ │
│ │ Order ID: #BTC240823001                                                 │ │
│ │                                                                         │ │
│ │ [📊 View Position] [🔔 Set Alerts]                                      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ │ Background: #F0FDF9 (ProfitGreen-50)                                     │ │
│ │ Border: 1px solid #BBF7D0 (ProfitGreen-200)                              │ │
│ │ Icon: ✅ 20px, #22C55E (ProfitGreen-500)                                 │ │
│ │ Text: #15803D (ProfitGreen-700)                                          │ │
│                                                                             │
│ Warning Alert Card:                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ⚠️ Portfolio Risk Alert                                     [✕ Dismiss] │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ Your portfolio allocation exceeds recommended risk levels.              │ │
│ │ Consider rebalancing or reducing position sizes.                        │ │
│ │                                                                         │ │
│ │ [⚖️ Rebalance] [📊 View Risk Analysis]                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ │ Background: #FFFBEB (CautionAmber-50)                                    │ │
│ │ Border: 1px solid #FDE68A (CautionAmber-200)                             │ │
│ │ Icon: ⚠️ 20px, #F59E0B (CautionAmber-500)                                │ │
│ │ Text: #B45309 (CautionAmber-700)                                         │ │
│                                                                             │
│ Error Alert Card:                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ❌ Connection Lost                                          [✕ Dismiss] │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ Unable to connect to market data. Real-time updates                     │ │
│ │ are currently unavailable. Please check your connection.                │ │
│ │                                                                         │ │
│ │ [🔄 Retry Connection] [📞 Support]                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ │ Background: #FEF2F2 (LossRed-50)                                         │ │
│ │ Border: 1px solid #FECACA (LossRed-200)                                  │ │
│ │ Icon: ❌ 20px, #EF4444 (LossRed-500)                                     │ │
│ │ Text: #B91C1C (LossRed-700)                                              │ │
│                                                                             │
│ Info Alert Card:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ℹ️ AI Model Updated                                         [✕ Dismiss] │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ Layer 2 AI model has been updated with improved accuracy.               │ │
│ │ Sector predictions are now 12% more reliable.                           │ │
│ │                                                                         │ │
│ │ [📊 View Improvements] [🤖 Learn More]                                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ │ Background: #FAF5FF (TechPurple-50)                                      │ │
│ │ Border: 1px solid #E9D5FF (TechPurple-200)                               │ │
│ │ Icon: ℹ️ 20px, #A855F7 (TechPurple-500)                                 │ │
│ │ Text: #7C3AED (TechPurple-700)                                           │ │
└─────────────────────────────────────────────────────────────────────────────┘

📱 RESPONSIVE CARD BEHAVIOR:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Desktop (1024px+):                                                          │
│ ├── Padding: 20px                                                          │
│ ├── Border Radius: 12px                                                    │
│ ├── Hover Effects: Full transform and shadow                               │
│ ├── Typography: Standard sizes                                             │
│ └── Grid: Multiple cards per row                                           │
│                                                                             │
│ Tablet (768px - 1023px):                                                   │
│ ├── Padding: 16px                                                          │
│ ├── Border Radius: 10px                                                    │
│ ├── Hover Effects: Reduced transform                                       │
│ ├── Typography: Slightly smaller                                           │
│ └── Grid: 2 cards per row maximum                                          │
│                                                                             │
│ Mobile (320px - 767px):                                                    │
│ ├── Padding: 16px                                                          │
│ ├── Border Radius: 8px                                                     │
│ ├── Hover Effects: None (touch-based)                                      │
│ ├── Typography: Mobile-optimized sizes                                     │
│ ├── Grid: Single column layout                                             │
│ ├── Touch Targets: Minimum 44px height                                     │
│ └── Swipe Actions: Support swipe gestures for actions                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 **Data Visualization Components (بعدازظهر - 4 ساعت)**

### **📈 Charts: Line, Bar, Pie Chart Styles (2 ساعت)**

#### **📈 Line Chart Specifications**
```
LINE CHART COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💹 PRICE CHART (Primary Use Case):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Price Chart Layout:                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟡 BTC/USD • $43,567 (+2.3%) • 4H Chart               🔍 ⚙️ 📤       │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │ $44,000 ┤                                                           ┌─┐ │ │
│ │         │                                                    ┌──────┘ │ │ │
│ │ $43,500 ┤                                             ┌──────┘        │ │ │
│ │         │                                      ┌──────┘               │ │ │
│ │ $43,000 ┤                               ┌──────┘                      │ │ │
│ │         │                        ┌──────┘                             │ │ │
│ │ $42,500 ┤                 ┌──────┘                                    │ │ │
│ │         │          ┌──────┘                                           │ │ │
│ │ $42,000 ┤   ┌──────┘                                                  │ │ │
│ │         └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴─ │ │
│ │         06:00   12:00   18:00   00:00   06:00   12:00   18:00   Now   │ │
│ │                                                                         │ │
│ │ Volume ████ ██ ████ ███ █████ ██ ████ ███ ████ ██ ███ ████ █████      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Visual Specifications:                                                      │
│ ├── Chart Area: #FFFFFF background, #F3F4F6 grid lines                     │
│ ├── Line Color: #0B8AFF (CryptoBlue-500), 2px thickness                    │
│ ├── Fill Area: linear-gradient from line color to transparent              │
│ ├── Grid: #E5E7EB horizontal lines, #F3F4F6 vertical lines                 │
│ ├── Axes: #6B7280 color, Inter Regular 12px                                │
│ ├── Crosshair: #64748B with white background tooltip                       │
│ ├── Data Points: 4px circles on hover, same color as line                  │
│ └── Animation: Smooth line drawing from left to right (1s)                 │
│                                                                             │
│ Interactive Features:                                                       │
│ ├── Hover: Show exact price, time, and volume                              │
│ ├── Zoom: Mouse wheel and touch pinch/zoom                                 │
│ ├── Pan: Click and drag to navigate time periods                           │
│ ├── Timeframe: 1m, 5m, 15m, 1h, 4h, 1d, 1w buttons                       │
│ ├── Indicators: Toggle MA, RSI, MACD overlays                              │
│ ├── Export: PNG, SVG, or data export functionality                         │
│ └── Fullscreen: Expand to modal view for detailed analysis                 │
└─────────────────────────────────────────────────────────────────────────────┘

📊 MULTI-SERIES LINE CHART:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Portfolio Comparison Chart:                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Portfolio vs Market Performance • 30 Days        [Legend] 🔍 ⚙️ 📤  │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ 15% ┤                                            ●●●●●●●●●●●●          │ │
│ │     │                                        ●●●●            ●●●●      │ │
│ │ 10% ┤                                    ●●●●                    ●●    │ │
│ │     │                                ●●●●                          ●   │ │
│ │  5% ┤                            ●●●●                               ● │ │
│ │     │                        ●●●●                                     │ │
│ │  0% ┤●●●●●●●●●●●●●●●●●●●●●●●●●●                                      │ │
│ │     │        ████████████████████████████████████████████████████████  │ │
│ │ -5% ┤                                                                  │ │
│ │     └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─ │ │
│ │     Aug 1    Aug 8    Aug 15   Aug 22   Aug 29    Today              │ │
│ │                                                                         │ │
│ │ Legend: ●●● My Portfolio (+12.4%)  ████ BTC Market (+5.2%)             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Multi-Series Configuration:                                                 │
│ ├── Series 1: #0B8AFF (CryptoBlue-500) - Portfolio performance            │
│ ├── Series 2: #F59E0B (CautionAmber-500) - Market benchmark               │
│ ├── Series 3: #22C55E (ProfitGreen-500) - AI predictions                  │
│ ├── Series 4: #A855F7 (TechPurple-500) - Additional comparison            │
│ ├── Line Styles: Solid, dashed, dotted for differentiation                │
│ ├── Opacity: 0.8 for lines, 0.3 for fill areas                            │
│ └── Legend: Toggle series visibility, color coding                        │
│                                                                             │
│ Advanced Features:                                                          │
│ ├── Y-Axis Sync: Multiple axes for different data scales                   │
│ ├── Annotations: Mark significant events on timeline                       │
│ ├── Brush Selection: Select time ranges for detailed analysis              │
│ ├── Real-time Updates: Live data streaming with smooth transitions         │
│ └── Comparison Mode: Normalize all series to same starting point           │
└─────────────────────────────────────────────────────────────────────────────┘

⚡ PERFORMANCE OPTIMIZATION:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Chart Performance Features:                                                 │
│ ├── Data Virtualization: Render only visible data points                   │
│ ├── Lazy Loading: Load data progressively as user zooms/pans               │
│ ├── Canvas Rendering: Use Canvas for large datasets (>1000 points)         │
│ ├── SVG for Interaction: Use SVG for smaller datasets with rich interaction │
│ ├── Debounced Updates: Batch real-time updates to prevent flickering       │
│ ├── Memory Management: Clear unused chart instances                        │
│ └── Responsive Breakpoints: Simplify charts on mobile devices              │
│                                                                             │
│ Mobile Optimizations:                                                       │
│ ├── Touch Gestures: Pinch to zoom, two-finger pan                          │
│ ├── Simplified UI: Hide advanced controls on mobile                        │
│ ├── Larger Touch Targets: Increase interactive area sizes                  │
│ ├── Reduced Data Density: Show fewer data points for clarity               │
│ └── Optimized Rendering: Lower frame rates for battery conservation        │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **📊 Bar Chart Specifications**
```
BAR CHART COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 VOLUME BAR CHART:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trading Volume Analysis:                                                    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 24H Trading Volume by Asset                         🔍 ⚙️ 📤        │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ $500M ┤                                                                 │ │
│ │       │                                                                 │ │
│ │ $400M ┤     ██████████████                                              │ │
│ │       │     ██████████████                                              │ │
│ │ $300M ┤     ██████████████  ████████████████                            │ │
│ │       │     ██████████████  ████████████████                            │ │
│ │ $200M ┤     ██████████████  ████████████████  ██████████                │ │
│ │       │     ██████████████  ████████████████  ██████████                │ │
│ │ $100M ┤     ██████████████  ████████████████  ██████████  ██████        │ │
│ │       │     ██████████████  ████████████████  ██████████  ██████        │ │
│ │    $0 └─────██████████████──████████████████──██████████──██████────── │ │
│ │             🟡 BTC          🔷 ETH          🔵 BNB        ⚪ ADA        │ │
│ │             $428M           $312M           $186M        $94M          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Bar Styling:                                                                │
│ ├── Bar Colors: Use asset-specific colors from palette                     │
│ ├── Bar Width: 48px (Desktop), 32px (Mobile)                               │
│ ├── Bar Spacing: 24px between bars                                         │
│ ├── Border Radius: 4px top corners for modern look                         │
│ ├── Gradient Fill: Subtle top-to-bottom gradient                           │
│ ├── Hover Effect: Lighten by 10%, show value tooltip                       │
│ └── Animation: Bars grow from bottom with staggered timing                 │
│                                                                             │
│ Data Labels:                                                                │
│ ├── Position: Center bottom of each bar                                    │
│ ├── Font: Inter Medium (500), 12px                                         │
│ ├── Color: #334155 (NightSlate-700)                                        │
│ ├── Format: Currency with smart abbreviation (M, B, K)                     │
│ └── Responsive: Hide on mobile if bars too narrow                          │
└─────────────────────────────────────────────────────────────────────────────┘

📊 HORIZONTAL BAR CHART (Rankings):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance Rankings:                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏆 Top Performers (24H) • Sorted by % Change          🔍 ⚙️ 📤         │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ 🟢 LINK ████████████████████████████████████████████████ +18.7%       │ │
│ │                                                                         │ │
│ │ 🟣 SOL  ████████████████████████████████████████ +14.2%                │ │
│ │                                                                         │ │
│ │ 🔷 ETH  ████████████████████████████████ +11.8%                        │ │
│ │                                                                         │ │
│ │ 🟡 BTC  ██████████████████████ +8.3%                                   │ │
│ │                                                                         │ │
│ │ 🔵 BNB  ████████████████ +5.9%                                         │ │
│ │                                                                         │ │
│ │ ⚪ ADA  ████████ +2.7%                                                  │ │
│ │                                                                         │ │
│ │ 🟤 DOT  ██ +0.4%                                                       │ │
│ │                                                                         │ │
│ │ 🔴 DOGE ░░░░░░░░ -3.2%                                                  │ │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Horizontal Bar Features:                                                    │
│ ├── Asset Icons: 24px crypto icons on the left                             │
│ ├── Asset Names: Inter Medium (500), 14px                                  │
│ ├── Bar Height: 32px with 8px spacing                                      │
│ ├── Progress Bars: Relative to highest value                               │
│ ├── Color Coding: Green for positive, red for negative                     │
│ ├── Value Labels: Right-aligned, outside bars                              │
│ ├── Hover State: Highlight entire row, show additional metrics             │
│ └── Sort Options: By value, alphabetical, or custom order                  │
│                                                                             │
│ Negative Value Handling:                                                    │
│ ├── Negative bars extend left from center axis                             │
│ ├── Use red color family for negative values                               │
│ ├── Add subtle pattern or transparency for distinction                     │
│ └── Clear zero line as visual anchor                                       │
└─────────────────────────────────────────────────────────────────────────────┘

📊 STACKED BAR CHART:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Portfolio Allocation Breakdown:                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🎯 Portfolio Distribution • Last 6 Months              🔍 ⚙️ 📤         │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ 100% ┤████████████████████████████████████████████████████████████████ │ │
│ │      │████████████████████████████████████████████████████████████████ │ │
│ │  80% ┤████████████████████████████████████████████████████████████████ │ │
│ │      │████████████████████████████████████████████████████████████████ │ │
│ │  60% ┤████████████████████████████████████████████████████████████████ │ │
│ │      │████████████████████████████████████████████████████████████████ │ │
│ │  40% ┤████████████████████████████████████████████████████████████████ │ │
│ │      │████████████████████████████████████████████████████████████████ │ │
│ │  20% ┤████████████████████████████████████████████████████████████████ │ │
│ │      │████████████████████████████████████████████████████████████████ │ │
│ │   0% └────────────────────────────────────────────────────────────────│ │
│ │      Mar     Apr     May     Jun     Jul     Aug     Now              │ │
│ │                                                                         │ │
│ │ Legend: ████ BTC (40%) ████ ETH (25%) ████ Others (35%)                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Stacked Bar Configuration:                                                  │
│ ├── Segment Colors: Use consistent asset color palette                     │
│ ├── Segment Order: Largest to smallest for visual stability                │
│ ├── Hover Interaction: Highlight segment, show percentage                  │
│ ├── Tooltip: Show exact values and percentages                             │
│ ├── Animation: Segments grow proportionally                                │
│ ├── Legend: Interactive, click to hide/show segments                       │
│ └── Responsive: Stack legend below chart on mobile                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **🥧 Pie Chart Specifications**
```
PIE CHART COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥧 PORTFOLIO ALLOCATION PIE CHART:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Current Portfolio Distribution:                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 💼 Portfolio Allocation • Total: $127,450              🔍 ⚙️ 📤         │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │              ╭─────────────────╮                                        │ │
│ │          ╭───┴───╮         ╭───┴───╮                                    │ │
│ │       ╭──┴───╮   │      ╭──┴───╮   │                                    │ │
│ │    ╭──┴──╮   │   │   ╭──┴──╮   │   │                                    │ │
│ │   ╱      ╲   │   │  ╱      ╲   │   │                                    │ │
│ │  ╱  🟡40% ╲  │   │ ╱  🔷25% ╲  │   │                                    │ │
│ │ ╱   BTC   ╲  │   │╱   ETH   ╲  │   │                                    │ │
│ │ ╲        ╱   │   │╲        ╱   │   │                                    │ │
│ │  ╲      ╱    │   │ ╲      ╱    │   │                                    │ │
│ │   ╲____╱  Others  ╲____╱      │   │                                    │ │
│ │          35%                   │   │                                    │ │
│ │          ╲____________________╱   │                                    │ │
│ │                                   │                                    │ │
│ │ Breakdown:                        │                                    │ │
│ │ 🟡 Bitcoin (BTC)      $51,000 (40.0%)                                  │ │
│ │ 🔷 Ethereum (ETH)     $31,863 (25.0%)                                  │ │
│ │ 🔵 Binance Coin (BNB) $12,745 (10.0%)                                  │ │
│ │ 🟣 Solana (SOL)       $10,196 (8.0%)                                   │ │
│ │ ⚪ Others (12 assets)  $21,646 (17.0%)                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Visual Specifications:                                                      │
│ ├── Chart Size: 240px diameter (Desktop), 200px (Mobile)                   │
│ ├── Slice Colors: Use asset-specific color palette                         │
│ ├── Slice Borders: 2px white borders between slices                        │
│ ├── Start Angle: 12 o'clock position (top)                                 │
│ ├── Sort Order: Largest to smallest clockwise                              │
│ ├── Minimum Slice: 3% minimum visible slice size                           │
│ ├── Small Slices: Group <3% slices into "Others" category                  │
│ └── Animation: Slices draw in clockwise with 0.5s stagger                  │
│                                                                             │
│ Interactive Features:                                                       │
│ ├── Hover: Highlight slice, scale up 5%, show tooltip                      │
│ ├── Click: Select slice, show detailed breakdown                           │
│ ├── Labels: Percentage inside slice if space allows                        │
│ ├── Legend: External legend with values and percentages                    │
│ ├── Explode: Pull out selected slice by 10px                               │
│ └── Drill-down: Click "Others" to see expanded breakdown                   │
└─────────────────────────────────────────────────────────────────────────────┘

🍩 DONUT CHART WITH CENTER METRIC:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Portfolio Performance Donut:                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Performance Distribution • 30 Days              🔍 ⚙️ 📤             │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │                        ╭─────────────╮                                  │ │
│ │                    ╭───┴─────────────┴───╮                              │ │
│ │                ╭───┴───╮           ╭───┴───╮                            │ │
│ │             ╭──┴───╮   │           │   ╱───┴──╮                         │ │
│ │          ╱──┴──╲   │   │    📈    │  ╱       ╲                         │ │
│ │         ╱       ╲  │   │           │ ╱         ╲                        │ │
│ │        ╱  🟢65%  ╲ │   │  +12.4%  │╱   🔴8%   ╲                       │ │
│ │       ╱ Positive ╲ │   │          │   Negative ╲                       │ │
│ │       ╲         ╱  │   │  Total   │╲          ╱                        │ │
│ │        ╲       ╱   │   │          │ ╲        ╱                         │ │
│ │         ╲_____╱    │   │   Gain   │  ╲______╱                          │ │
│ │             ╲      │   │          │      ╱                             │ │
│ │              ╲_____│___│__________│_____╱                              │ │
│ │                    ╲   🟡27%     ╱                                      │ │
│ │                     ╲  Neutral  ╱                                       │ │
│ │                      ╲_________╱                                        │ │
│ │                                                                         │ │
│ │ Asset Breakdown:                                                        │ │
│ │ 🟢 Positive (65%): 8 assets with gains                                  │ │
│ │ 🟡 Neutral (27%): 3 assets flat                                        │ │
│ │ 🔴 Negative (8%): 2 assets with losses                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Donut Chart Features:                                                       │
│ ├── Inner Radius: 40% of outer radius for donut hole                       │
│ ├── Center Content: Key metric with icon and value                         │
│ ├── Center Typography: Inter SemiBold (600), 24px value                    │
│ ├── Center Subtext: Inter Regular (400), 14px description                  │
│ ├── Slice Thickness: Consistent 48px thickness                             │
│ ├── Gradient Fills: Subtle radial gradients for depth                      │
│ ├── Active Slice: Highlight on hover, update center content                │
│ └── Responsive Center: Scale center content with chart size                │
│                                                                             │
│ Multi-Layer Donut:                                                          │
│ ├── Inner Ring: Main categories (40px thickness)                           │
│ ├── Outer Ring: Subcategories (24px thickness)                             │
│ ├── Spacing: 4px gap between rings                                         │
│ ├── Alignment: Subcategories align with parent segments                    │
│ └── Interaction: Click inner to show/hide outer ring                       │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 ACCESSIBILITY & RESPONSIVENESS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Accessibility Features:                                                     │
│ ├── ARIA Labels: Proper roles and descriptions for screen readers          │
│ ├── Keyboard Navigation: Tab through slices, Enter to select               │
│ ├── Color Independence: Patterns and labels not just color-coded           │
│ ├── High Contrast: Ensure sufficient contrast for all text                 │
│ ├── Focus Indicators: Clear visual focus states                            │
│ └── Alternative Data: Table view option for screen readers                 │
│                                                                             │
│ Responsive Behavior:                                                        │
│ ├── Desktop (1024px+): Full size with external legend                      │
│ ├── Tablet (768-1023px): Medium size, legend below                         │ │
│ ├── Mobile (320-767px): Compact size, simplified legend                    │ │
│ ├── Touch Optimization: Larger touch targets on mobile                     │ │
│ ├── Gesture Support: Pinch to zoom on complex charts                       │ │
│ └── Performance: Reduce animation complexity on low-end devices            │ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **📋 Tables: Data Table, Responsive Table Design (1 ساعت)**

#### **📊 Data Table Specifications**
```
DATA TABLE COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 FINANCIAL DATA TABLE:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Watchlist Table:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 💰 Tier 1 Watchlist • 7 Assets                     🔍 📊 ⚙️ 📤         │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │ Asset      │ Price      │ 24h Change │ Volume     │ AI Score │ Action  │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🟡 Bitcoin │ $43,567.89 │ 📈 +2.3%   │ $428M      │ 94/100   │ [View]  │ │
│ │    BTC     │            │ (+$978)    │            │ ●●●●●    │ [Trade] │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🔷 Ethereum│ $2,847.23  │ 📈 +3.1%   │ $312M      │ 91/100   │ [View]  │ │
│ │    ETH     │            │ (+$85)     │            │ ●●●●●    │ [Trade] │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🔵 Chainlink│ $14.56     │ 📈 +4.2%   │ $89M       │ 89/100   │ [View]  │ │
│ │    LINK    │            │ (+$0.59)   │            │ ●●●●○    │ [Trade] │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🔶 Uniswap │ $6.45      │ 📈 +1.8%   │ $54M       │ 86/100   │ [View]  │ │
│ │    UNI     │            │ (+$0.11)   │            │ ●●●●○    │ [Trade] │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🟤 Polkadot│ $5.23      │ 📉 -0.5%   │ $32M       │ 78/100   │ [View]  │ │
│ │    DOT     │            │ (-$0.03)   │            │ ●●●○○    │ [Trade] │ │
│ │────────────┼────────────┼────────────┼────────────┼──────────┼─────────│ │
│ │ 🔴 Dogecoin│ $0.0745    │ 📉 -3.2%   │ $28M       │ 45/100   │ [View]  │ │
│ │    DOGE    │            │ (-$0.0025) │            │ ●●○○○    │ [Short] │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Table Structure:                                                            │
│ ├── Header: Fixed header with sorting controls                             │
│ ├── Row Height: 64px for comfortable touch targets                         │
│ ├── Alternating Rows: #F8FAFC background for odd rows                      │
│ ├── Borders: 1px solid #E2E8F0 between rows                                │
│ ├── Padding: 16px horizontal, 12px vertical                                │
│ ├── Typography: JetBrains Mono for numbers, Inter for text                 │
│ └── Hover State: #F1F5F9 background on row hover                           │
│                                                                             │
│ Column Specifications:                                                      │
│ ├── Asset: 140px, icon + name + symbol                                     │
│ ├── Price: 120px, right-aligned numbers                                    │
│ ├── Change: 120px, colored indicators with arrows                          │
│ ├── Volume: 100px, abbreviated notation (M, B)                             │
│ ├── AI Score: 100px, visual progress bars                                  │
│ ├── Actions: 120px, button group                                           │
│ └── Responsive: Hide less critical columns on narrow screens               │
│                                                                             │
│ Sorting & Filtering:                                                        │
│ ├── Sort Icons: ↑↓ arrows in column headers                                │
│ ├── Multi-Sort: Hold Shift for secondary sorting                           │
│ ├── Search: Global search bar with real-time filtering                     │
│ ├── Column Filter: Individual column filter dropdowns                      │
│ ├── Quick Filters: Buttons for common filters (Gainers, Losers)            │
│ └── Save Views: Save custom sort/filter combinations                       │
└─────────────────────────────────────────────────────────────────────────────┘

📱 RESPONSIVE TABLE TRANSFORMATIONS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Desktop View (1024px+):                                                    │
│ ├── Full table with all columns visible                                    │
│ ├── Fixed header with horizontal scroll if needed                          │
│ ├── Row height: 64px                                                       │
│ ├── Hover effects and detailed tooltips                                    │
│ └── Context menus on right-click                                           │
│                                                                             │
│ Tablet View (768-1023px):                                                  │
│ ├── Hide Volume column, keep essential data                                │
│ ├── Compress AI Score to icon only                                         │
│ ├── Simplify action buttons to single menu                                 │
│ ├── Row height: 56px                                                       │
│ └── Touch-optimized controls                                               │
│                                                                             │
│ Mobile View (320-767px):                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 💰 Watchlist (7)                               🔍 ⚙️                   │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟡 Bitcoin (BTC)                                            [●●●] │ │ │
│ │ │ $43,567.89    📈 +2.3% (+$978)                              94/100 │ │ │
│ │ │ Volume: $428M                                      [View] [Trade] │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🔷 Ethereum (ETH)                                           [●●●] │ │ │
│ │ │ $2,847.23     📈 +3.1% (+$85)                               91/100 │ │ │
│ │ │ Volume: $312M                                      [View] [Trade] │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🔴 Dogecoin (DOGE)                                          [●●○] │ │ │
│ │ │ $0.0745       📉 -3.2% (-$0.0025)                           45/100 │ │ │
│ │ │ Volume: $28M                                      [View] [Short] │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Mobile Card Features:                                                       │
│ ├── Card Layout: Each row becomes a card                                   │
│ ├── Stacked Information: Vertical data layout                              │
│ ├── Large Touch Targets: 44px minimum                                      │
│ ├── Swipe Actions: Swipe left/right for quick actions                      │
│ ├── Pull to Refresh: Update data with pull gesture                         │
│ ├── Infinite Scroll: Load more data as user scrolls                        │
│ └── Simplified Interactions: Reduce cognitive load                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **📈 Indicators: Status Indicators, Progress Bars (1 ساعت)**

#### **🔴 Status Indicator Specifications**
```
STATUS INDICATOR COMPONENT SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 SYSTEM STATUS INDICATORS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ AI System Health:                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🤖 AI System Status                                           [Details] │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │                                                                         │ │
│ │ 🟢 Layer 1 (Macro)      ● Online     87% Accuracy    ↗️ Improving      │ │
│ │ 🟢 Layer 2 (Sector)     ● Online     84% Accuracy    → Stable          │ │
│ │ 🟡 Layer 3 (Assets)     ● Warning    78% Accuracy    ↘️ Declining       │ │
│ │ 🔴 Layer 4 (Timing)     ● Offline    --% Accuracy    🔧 Maintenance     │ │
│ │                                                                         │ │
│ │ 📊 Overall System: 🟡 Degraded (3/4 layers operational)                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Status Dot Specifications:                                                  │
│ ├── Size: 8px diameter (Small), 12px (Medium), 16px (Large)                │
│ ├── Colors: Success, Warning, Error, Info, Neutral                         │
│ ├── Animation: 2s pulse for attention states                               │
│ ├── Position: Inline with text or standalone                               │
│ └── Accessibility: Paired with text labels                                 │
│                                                                             │
│ Status Colors:                                                              │
│ ├── 🟢 Online/Healthy: #22C55E (ProfitGreen-500)                          │
│ ├── 🟡 Warning/Degraded: #F59E0B (CautionAmber-500)                       │
│ ├── 🔴 Offline/Error: #EF4444 (LossRed-500)                               │
│ ├── 🔵 Info/Processing: #0B8AFF (CryptoBlue-500)                          │
│ ├── ⚪ Unknown/Disabled: #94A3B8 (NightSlate-400)                          │
│ └── 🟣 Special/AI: #A855F7 (TechPurple-500)                               │
│                                                                             │
│ Animation Patterns:                                                         │
│ ├── Pulse: Breathing effect for warnings                                   │
│ ├── Blink: Fast flash for critical alerts                                  │
│ ├── Fade: Gentle fade for informational states                             │
│ ├── Static: No animation for stable states                                 │
│ └── Spin: Loading or processing indicators                                 │
└─────────────────────────────────────────────────────────────────────────────┘

📊 PROGRESS BAR COMPONENTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ AI Confidence Progress Bar:                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🧠 AI Confidence Level                                                  │ │
│ │                                                                         │ │
│ │ Signal Confidence: 87%                                                  │ │
│ │ ████████████████████████████████████████▒▒▒▒▒▒▒▒                       │ │
│ │ ↑ Very High                                                             │ │
│ │                                                                         │ │
│ │ Risk Assessment: 34%                                                    │ │
│ │ ████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒                               │ │
│ │ ↑ Low-Medium                                                            │ │
│ │                                                                         │ │
│ │ Model Accuracy: 94%                                                     │ │
│ │ ██████████████████████████████████████████████▒▒▒▒                     │ │
│ │ ↑ Excellent                                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Progress Bar Structure:                                                     │
│ ├── Container: Rounded rectangle, 8px height                               │
│ ├── Background: #E2E8F0 (NightSlate-200)                                   │
│ ├── Fill: Gradient based on value and context                              │
│ ├── Border Radius: 4px for modern appearance                               │
│ ├── Animation: Smooth fill on load (1s ease-out)                           │
│ ├── Label: Above or inline with percentage                                 │
│ └── Indicator: Optional descriptive text below                             │
│                                                                             │
│ Progress Colors (Context-Based):                                            │
│ ├── Performance: Green gradient (low → high)                               │
│ ├── Risk: Red gradient (low → high)                                        │
│ ├── Confidence: Blue gradient (low → high)                                 │
│ ├── Accuracy: Purple gradient (low → high)                                 │
│ └── Generic: Gray to blue gradient                                         │
│                                                                             │
│ Size Variants:                                                              │
│ ├── Mini: 4px height, no labels                                            │
│ ├── Small: 6px height, percentage only                                     │
│ ├── Medium: 8px height, full labels                                        │
│ ├── Large: 12px height, descriptive text                                   │
│ └── Hero: 16px height, prominent display                                   │
└─────────────────────────────────────────────────────────────────────────────┘

⚡ LOADING INDICATORS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Loading Spinner Variants:                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Data Loading States:                                                    │ │
│ │                                                                         │ │
│ │ ⟳ Loading market data...        [Rotating spinner + text]              │ │
│ │                                                                         │ │
│ │ 🤖 AI analyzing...              [Pulsing brain icon]                    │ │
│ │                                                                         │ │
│ │ ▓▓▓▓▓▓▒▒▒▒ 60%                  [Progress bar with percentage]           │ │
│ │ Processing signals...                                                   │ │
│ │                                                                         │ │
│ │ ●●●○○○○○○○                       [Dots progress indicator]              │ │
│ │ Step 3 of 10                                                            │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Spinner Types:                                                              │
│ ├── Circular: Classic rotating circle                                      │
│ ├── Dots: Three bouncing dots                                              │
│ ├── Pulse: Growing/shrinking circle                                        │
│ ├── Bars: Animated height bars                                             │
│ ├── Gradient: Rotating gradient ring                                       │
│ └── Custom: Brand-specific animations                                      │
│                                                                             │
│ Loading Context:                                                            │
│ ├── Page Load: Full page spinner overlay                                   │
│ ├── Component Load: Local component spinner                                │
│ ├── Button Load: Inline button spinner                                     │
│ ├── Data Refresh: Subtle refresh indicator                                 │
│ ├── AI Processing: Specialized AI animation                                │
│ └── Background: Non-blocking background indicator                          │
│                                                                             │
│ Accessibility:                                                              │
│ ├── ARIA Label: "Loading" with descriptive text                            │
│ ├── Screen Reader: Announce loading state changes                          │
│ ├── Focus Management: Trap focus during loading                            │
│ ├── Timeout: Show progress for long operations                             │
│ └── Error States: Clear error messages if loading fails                    │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 METRIC BADGES & INDICATORS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Performance Metric Badges:                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Portfolio Metrics:                                                      │ │
│ │                                                                         │ │
│ │ 📈 Performance  [🟢 +12.4%]  [📊 Excellent]  [⭐ 4.8/5]                │ │
│ │                                                                         │ │
│ │ 🛡️ Risk Level   [🟡 Medium]   [📊 Moderate]   [⚠️ 3.2/7]                │ │
│ │                                                                         │ │
│ │ 🤖 AI Accuracy  [🟢 87%]      [📊 High]       [✅ Reliable]             │ │
│ │                                                                         │ │
│ │ 🔄 Last Update  [🟢 Live]     [📊 Real-time]  [⚡ < 1min]               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Badge Specifications:                                                       │
│ ├── Size: 24px height, auto width with 8px padding                         │
│ ├── Typography: Inter Medium (500), 12px                                   │
│ ├── Colors: Match semantic color system                                    │
│ ├── Border Radius: 12px (pill shape)                                       │
│ ├── Icon: 16px icon on left with 4px margin                                │
│ ├── Hover: Slight scale transform and tooltip                              │
│ └── Click: Optional click action for details                               │
│                                                                             │
│ Badge Types:                                                                │
│ ├── Status: Online/Offline, Active/Inactive                                │
│ ├── Performance: Percentage or rating values                               │
│ ├── Category: Classification or grouping                                   │
│ ├── Priority: High/Medium/Low importance                                   │
│ ├── Count: Notification count or quantity                                  │
│ └── Custom: Brand or feature-specific badges                               │
│                                                                             │
│ Notification Badges:                                                        │
│ ├── Position: Top-right corner of parent element                           │
│ ├── Size: 20px circle for numbers, auto for text                           │
│ ├── Color: #EF4444 (LossRed-500) for alerts                               │
│ ├── Text: White text, Inter Bold (700), 11px                               │
│ ├── Animation: Bounce in when new notification arrives                     │
│ └── Max Count: Show "99+" for counts over 99                               │
└─────────────────────────────────────────────────────────────────────────────┘
```
