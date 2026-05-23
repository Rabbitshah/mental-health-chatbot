import { useEffect, useState } from "react";
import {
  AlertTriangle,
  HeartHandshake,
  Phone,
  Plus,
  Save,
  ShieldCheck,
  Trash2,
  Users,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import API from "../api";
import { showToast } from "../components/Toast";

const sections = [
  {
    key: "warning_signs",
    title: "Warning Signs",
    helper: "Early signs that tell you extra support may help.",
    icon: AlertTriangle,
    placeholder: "Example: I stop replying to people",
  },
  {
    key: "coping_strategies",
    title: "Coping Steps",
    helper: "Things you can do on your own for the next few minutes.",
    icon: ShieldCheck,
    placeholder: "Example: Take a shower or use box breathing",
  },
  {
    key: "trusted_contacts",
    title: "Trusted People",
    helper: "People you can message or call when things feel unsafe.",
    icon: Users,
    placeholder: "Example: Maya - 555-1234",
  },
  {
    key: "professional_contacts",
    title: "Professional Support",
    helper: "Clinicians, campus support, local services, or hotlines.",
    icon: Phone,
    placeholder: "Example: Therapist office - 555-0100",
  },
  {
    key: "safe_environment_steps",
    title: "Safer Environment",
    helper: "Steps that create distance from anything risky.",
    icon: ShieldCheck,
    placeholder: "Example: Move to the living room",
  },
  {
    key: "reasons_to_stay",
    title: "Reasons To Stay",
    helper: "Personal anchors worth remembering in hard moments.",
    icon: HeartHandshake,
    placeholder: "Example: My sister, my music, tomorrow morning",
  },
];

const emptyPlan = sections.reduce((plan, section) => {
  plan[section.key] = [""];
  return plan;
}, {});

export default function SafetyPlan() {
  const [plan, setPlan] = useState(emptyPlan);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    API.get("/wellness/safety-plan")
      .then(({ data }) => {
        const nextPlan = { ...emptyPlan };
        sections.forEach((section) => {
          const values = data[section.key] || [];
          nextPlan[section.key] = values.length ? values : [""];
        });
        setPlan(nextPlan);
      })
      .catch(() => showToast("Could not load your safety plan."))
      .finally(() => setIsLoading(false));
  }, []);

  const updateItem = (key, index, value) => {
    setPlan((current) => ({
      ...current,
      [key]: current[key].map((item, itemIndex) =>
        itemIndex === index ? value : item,
      ),
    }));
  };

  const addItem = (key) => {
    setPlan((current) => ({
      ...current,
      [key]: [...current[key], ""],
    }));
  };

  const removeItem = (key, index) => {
    setPlan((current) => {
      const nextItems = current[key].filter((_, itemIndex) => itemIndex !== index);
      return {
        ...current,
        [key]: nextItems.length ? nextItems : [""],
      };
    });
  };

  const savePlan = async () => {
    setIsSaving(true);
    try {
      const payload = {};
      sections.forEach((section) => {
        payload[section.key] = plan[section.key]
          .map((item) => item.trim())
          .filter(Boolean);
      });
      const { data } = await API.put("/wellness/safety-plan", payload);
      const nextPlan = { ...emptyPlan };
      sections.forEach((section) => {
        nextPlan[section.key] = data[section.key]?.length ? data[section.key] : [""];
      });
      setPlan(nextPlan);
      showToast("Safety plan saved.", "success");
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save your safety plan.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-5 pb-24 md:p-10" style={{ background: "#F7FAFD" }}>
        <div className="max-w-[1180px] mx-auto space-y-6">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 text-sm" style={{ background: "rgba(224, 124, 107, 0.1)", color: "#C15A4B", borderRadius: "999px" }}>
                <ShieldCheck size={16} />
                Private crisis support plan
              </div>
              <h1 className="text-3xl md:text-4xl" style={{ color: "var(--aura-text-primary)" }}>
                Safety Plan
              </h1>
              <p className="mt-2 max-w-2xl" style={{ color: "var(--aura-text-secondary)" }}>
                Keep a clear, personal plan ready for moments when your thoughts feel intense or unsafe.
              </p>
            </div>
            <button
              onClick={savePlan}
              disabled={isSaving || isLoading}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 text-white transition-all disabled:opacity-50"
              style={{ background: "#2C5F8A", borderRadius: "12px" }}
            >
              <Save size={18} />
              {isSaving ? "Saving..." : "Save Plan"}
            </button>
          </header>

          <section className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-5">
              {sections.map((section) => (
                <PlanSection
                  key={section.key}
                  section={section}
                  items={plan[section.key] || [""]}
                  onAdd={() => addItem(section.key)}
                  onRemove={(index) => removeItem(section.key, index)}
                  onChange={(index, value) => updateItem(section.key, index, value)}
                />
              ))}
            </div>

            <aside className="space-y-5">
              <div className="bg-white p-6" style={{ borderRadius: "16px", border: "1px solid #E4ECF4" }}>
                <h2 className="text-xl mb-3" style={{ color: "var(--aura-text-primary)" }}>
                  Immediate Support
                </h2>
                <p className="text-sm mb-4" style={{ color: "var(--aura-text-secondary)" }}>
                  If there is immediate danger, use emergency support now.
                </p>
                <div className="space-y-3">
                  <a href="tel:988" className="flex items-center gap-3 p-4 text-white" style={{ background: "#E07C6B", borderRadius: "12px" }}>
                    <Phone size={18} />
                    <span>Call or Text 988</span>
                  </a>
                  <a href="sms:741741" className="flex items-center gap-3 p-4" style={{ color: "#2C5F8A", border: "1px solid #D0DCE8", borderRadius: "12px" }}>
                    <HeartHandshake size={18} />
                    <span>Text HOME to 741741</span>
                  </a>
                </div>
              </div>

              <div className="p-6" style={{ borderRadius: "16px", background: "#1C2B3A", color: "white" }}>
                <h2 className="text-xl mb-3">Use this plan when...</h2>
                <ul className="space-y-2 text-sm" style={{ color: "#D8E4EF" }}>
                  <li>You notice your warning signs.</li>
                  <li>You feel isolated or overwhelmed.</li>
                  <li>You need a prepared contact list.</li>
                  <li>You want one safer next step.</li>
                </ul>
              </div>
            </aside>
          </section>
        </div>
      </main>
    </div>
  );
}

function PlanSection({ section, items, onAdd, onRemove, onChange }) {
  const Icon = section.icon;
  return (
    <section className="bg-white p-5" style={{ borderRadius: "16px", border: "1px solid #E4ECF4" }}>
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(74, 144, 217, 0.1)", color: "#2C5F8A" }}>
          <Icon size={20} />
        </div>
        <div>
          <h2 className="text-lg" style={{ color: "var(--aura-text-primary)" }}>{section.title}</h2>
          <p className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>{section.helper}</p>
        </div>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={`${section.key}-${index}`} className="flex gap-2">
            <input
              value={item}
              onChange={(event) => onChange(index, event.target.value)}
              placeholder={section.placeholder}
              className="flex-1 px-3 py-2 text-sm focus:outline-none focus:ring-2"
              style={{ border: "1px solid #D0DCE8", borderRadius: "10px", color: "var(--aura-text-primary)" }}
            />
            <button
              type="button"
              onClick={() => onRemove(index)}
              className="w-10 h-10 inline-flex items-center justify-center"
              style={{ border: "1px solid #F1D1CC", borderRadius: "10px", color: "#E07C6B" }}
              aria-label="Remove item"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={onAdd}
        className="mt-4 inline-flex items-center gap-2 px-3 py-2 text-sm"
        style={{ color: "#2C5F8A", background: "rgba(74, 144, 217, 0.08)", borderRadius: "10px" }}
      >
        <Plus size={16} />
        Add item
      </button>
    </section>
  );
}
