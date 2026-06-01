import streamlit as st
import anthropic
import base64
import json
import re
from PIL import Image
import io
from datetime import date
from proposal_generator import generate_proposal_pdf

st.set_page_config(page_title="Solar Proposal Generator", page_icon="☀️", layout="wide")

st.title("☀️ Solar Proposal Generator")
st.caption("Upload a customer electricity bill → AI extracts data → Generates full PDF proposal")

# ── Sidebar: Company config ──────────────────────────────────────────────────
with st.sidebar:
    st.header("🏢 Company Settings")
    company_name = st.text_input("Company Name", value="EnergyBae Private Limited")
    company_tagline = st.text_input("Tagline", value="Empowering People with Renewable Energy Solutions")
    company_website = st.text_input("Website", value="www.energybae.in")
    company_phone = st.text_input("Phone", value="+91 7507991787 / 7744977420")
    company_email = st.text_input("Email", value="freeenergy@energybae.in")
    company_address = st.text_area("Address", value="PCISC, AutoCluster, MIDC, Opp. PCMC Science Park, Chinchwad, Pune - 411019")
    prepared_by = st.text_input("Prepared By", value="Akshay Jain")
    prepared_by_title = st.text_input("Title", value="Co-founder")

    st.divider()
    st.header("💰 Pricing Config")
    rate_per_kw = st.number_input("Rate per kW (₹)", value=70000, step=1000)
    gst_rate = st.number_input("GST Rate (%)", value=8.9, step=0.1)
    subsidy_per_kw = st.number_input("PMSGY Subsidy per kW (₹)", value=26000, step=1000)
    payback_period = st.text_input("Payback Period", value="< 2 Years & 3 Months")
    amc_years = st.number_input("Free AMC Years", value=5, step=1)

# ── Main: Bill upload ────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Step 1: Upload Electricity Bill")
    uploaded_file = st.file_uploader(
        "Upload bill image (JPG, PNG, PDF screenshot)",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Bill", use_container_width=True)

with col2:
    st.subheader("🤖 Step 2: AI Extracts Data")

    extracted = {}

    if uploaded_file:
        if st.button("⚡ Extract from Bill", type="primary", use_container_width=True):
            with st.spinner("Analysing bill with Claude Vision..."):
                try:
                    # Convert image to base64
                    img_bytes = uploaded_file.getvalue()
                    b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
                    ext = uploaded_file.name.split(".")[-1].lower()
                    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
                    mime = mime_map.get(ext, "image/jpeg")

                    client = anthropic.Anthropic()
                    response = client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {"type": "base64", "media_type": mime, "data": b64}
                                },
                                {
                                    "type": "text",
                                    "text": """Extract the following from this electricity bill. Return ONLY a valid JSON object, no markdown, no extra text.

{
  "customer_name": "full name of consumer",
  "customer_address": "full address",
  "consumer_number": "consumer/account number if visible",
  "sanctioned_load": "sanctioned load in kW (number only)",
  "monthly_units": "average monthly units consumed (number only)",
  "unit_rate": "cost per unit in rupees (number only)",
  "monthly_bill_amount": "total monthly bill amount in rupees (number only)",
  "meter_number": "meter number if visible or empty string"
}

If any field is not visible or unclear, use an empty string. For numeric fields use your best estimate based on visible data."""
                                }
                            ]
                        }]
                    )

                    raw = response.content[0].text.strip()
                    # strip markdown fences if present
                    raw = re.sub(r"```json|```", "", raw).strip()
                    extracted = json.loads(raw)
                    st.session_state["extracted"] = extracted
                    st.success("✅ Data extracted successfully!")

                except json.JSONDecodeError:
                    st.error("Could not parse AI response. Try a clearer image.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Show/edit extracted data
    if "extracted" in st.session_state:
        extracted = st.session_state["extracted"]
        st.write("**Review & edit extracted data:**")
        extracted["customer_name"] = st.text_input("Customer Name", value=extracted.get("customer_name", ""))
        extracted["customer_address"] = st.text_area("Customer Address", value=extracted.get("customer_address", ""), height=80)
        extracted["consumer_number"] = st.text_input("Consumer Number", value=extracted.get("consumer_number", ""))
        extracted["sanctioned_load"] = st.text_input("Sanctioned Load (kW)", value=str(extracted.get("sanctioned_load", "4")))
        extracted["monthly_units"] = st.text_input("Avg Monthly Units", value=str(extracted.get("monthly_units", "")))
        extracted["unit_rate"] = st.text_input("Unit Rate (₹/kWh)", value=str(extracted.get("unit_rate", "8")))
        extracted["monthly_bill_amount"] = st.text_input("Monthly Bill (₹)", value=str(extracted.get("monthly_bill_amount", "")))
        st.session_state["extracted"] = extracted

# ── Step 3: Configure proposal ───────────────────────────────────────────────
st.divider()
st.subheader("⚙️ Step 3: Configure Proposal")

col3, col4, col5 = st.columns(3)

with col3:
    proposed_capacity = st.number_input("Proposed Solar Capacity (kW)", value=3, min_value=1, max_value=100)
    installation_type = st.selectbox("Installation Type", ["Shed Mounted Structure", "RCC Roof Mounted", "Ground Mounted", "Tin Shed Mounted"])

with col4:
    panel_type = st.text_input("Panel Type", value="600 Wp Mono TOPCon Bi-facial DCR")
    panel_make = st.text_input("Panel Make", value="Premier or as equivalent")
    inverter_make = st.text_input("Inverter Make", value="Growatt or as equivalent")

with col5:
    proposal_number = st.text_input("Proposal Number", value=f"EBAE/QUO/26-27/{date.today().strftime('%d%m')}")
    proposal_date = st.date_input("Proposal Date", value=date.today())
    annual_irradiation = st.number_input("Annual Irradiation (kWh/m²)", value=2047.2)

# Calculate derived values
project_cost_subtotal = proposed_capacity * rate_per_kw
gst_amount = round(project_cost_subtotal * gst_rate / 100)
total_project_cost = project_cost_subtotal + gst_amount
total_subsidy = proposed_capacity * subsidy_per_kw
effective_amount = total_project_cost - total_subsidy

# Estimate annual generation (approx 1.2x capacity in kWh for Pune)
estimated_annual_gen = round(proposed_capacity * 1450)

# Estimate lifetime savings (25 years, unit rate from bill or default ₹8)
try:
    ur = float(st.session_state.get("extracted", {}).get("unit_rate", 8) or 8)
except:
    ur = 8.0
lifetime_savings = round(estimated_annual_gen * 25 * ur)

st.divider()
st.subheader("💵 Auto-Calculated Pricing")
pc1, pc2, pc3, pc4 = st.columns(4)
pc1.metric("Project Sub-Total", f"₹{project_cost_subtotal:,}")
pc2.metric(f"GST ({gst_rate}%)", f"₹{gst_amount:,}")
pc3.metric("Total (Payable)", f"₹{total_project_cost:,}")
pc4.metric("After Subsidy", f"₹{effective_amount:,}")

# ── Step 4: Generate PDF ─────────────────────────────────────────────────────
st.divider()
st.subheader("📥 Step 4: Generate Proposal PDF")

if st.button("🚀 Generate Full Proposal PDF", type="primary", use_container_width=True):
    if not st.session_state.get("extracted") and not st.session_state.get("manual_ok"):
        st.warning("No bill data extracted yet. Fill in customer details manually or extract from bill first.")
        st.session_state["manual_ok"] = True
    else:
        with st.spinner("Generating proposal PDF..."):
            try:
                data = {
                    # Customer
                    "customer_name": st.session_state.get("extracted", {}).get("customer_name", "Customer"),
                    "customer_address": st.session_state.get("extracted", {}).get("customer_address", ""),
                    "consumer_number": st.session_state.get("extracted", {}).get("consumer_number", ""),
                    "sanctioned_load": st.session_state.get("extracted", {}).get("sanctioned_load", "4"),
                    "unit_rate": ur,
                    "monthly_units": st.session_state.get("extracted", {}).get("monthly_units", ""),
                    # System
                    "proposed_capacity": proposed_capacity,
                    "panel_type": panel_type,
                    "panel_make": panel_make,
                    "inverter_make": inverter_make,
                    "installation_type": installation_type,
                    "annual_irradiation": annual_irradiation,
                    "estimated_annual_gen": estimated_annual_gen,
                    "payback_period": payback_period,
                    "lifetime_savings": lifetime_savings,
                    # Pricing
                    "rate_per_kw": rate_per_kw,
                    "project_cost_subtotal": project_cost_subtotal,
                    "gst_rate": gst_rate,
                    "gst_amount": gst_amount,
                    "total_project_cost": total_project_cost,
                    "total_subsidy": total_subsidy,
                    "effective_amount": effective_amount,
                    # Proposal meta
                    "proposal_number": proposal_number,
                    "proposal_date": proposal_date.strftime("%d %B %Y"),
                    "amc_years": amc_years,
                    # Company
                    "company_name": company_name,
                    "company_tagline": company_tagline,
                    "company_website": company_website,
                    "company_phone": company_phone,
                    "company_email": company_email,
                    "company_address": company_address,
                    "prepared_by": prepared_by,
                    "prepared_by_title": prepared_by_title,
                }

                pdf_bytes = generate_proposal_pdf(data)
                customer_slug = data["customer_name"].replace(" ", "_")
                filename = f"Solar_Proposal_{customer_slug}_{proposal_date.strftime('%Y%m%d')}.pdf"

                st.success("✅ Proposal generated!")
                st.download_button(
                    label="📥 Download PDF Proposal",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
                import traceback
                st.code(traceback.format_exc())
