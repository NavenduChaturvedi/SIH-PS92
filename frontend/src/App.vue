<script setup>
import { ref, onBeforeUnmount, computed, watch } from 'vue'
import axios from 'axios'
import { ArrowUpRight, Calculator, CircleAlert, Languages, MapPin, Mic, RotateCcw, SlidersHorizontal, Volume2 } from 'lucide-vue-next'
import { getStaticDemos, getStaticTexts } from './translations'
import rinudayIcon from './assets/rinuday-icon.png'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'https://sih-2026-26092-t2.onrender.com').replace(/\/+$/, '')
const languages = [
  { code: 'en', label: 'English', native: 'English', voiceCode: 'en-IN' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা', voiceCode: 'bn-IN' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी', voiceCode: 'hi-IN' },
  { code: 'mr', label: 'Marathi', native: 'मराठी', voiceCode: 'mr-IN' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்', voiceCode: 'ta-IN' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు', voiceCode: 'te-IN' }
]

const initialDemoTexts = [
  { id: 'demo1', label: 'Tailoring shop · ₹1.2L', text: 'I need 1.2 lakh rupees for a tailoring shop. My family earns 150000 a year.' },
  { id: 'demo2', label: 'Dairy farm · ₹3L', text: 'I want 3 lakh for a small dairy business. My income is 280000 annually.' },
  { id: 'demo3', label: 'Welding workshop · ₹5L', text: 'I need 5 lakh for a welding unit and earn 450000 per year.' },
  { id: 'demo4', label: 'Engineering college · ₹2L', text: 'I am a college student and need 2 lakh for my engineering course. My family earns 300000 a year.' }
]

const defaultTexts = {
  brandSubtitle: 'Intelligent concessional scheme matcher',
  location: 'India',
  eyebrowWorkspace: 'Financial assistance workspace',
  headingMain1: 'Good afternoon.',
  headingMain2: "Let's make your plan possible.",
  introCopy: 'Describe your requirement in your own words. We’ll turn it into an eligibility check and practical next steps.',
  metricRequired: 'Required',
  metricIncome: 'Annual income',
  metricSector: 'Sector',
  metricStatus: 'Current status',
  statusEligible: 'Eligible',
  statusReview: 'Review needed',
  statusReady: 'Ready to analyse',
  eyebrowSupport: 'Find support',
  titleLookingFor: "Tell us what you're looking for",
  btnStructured: 'Structured profile',
  btnNatural: 'Natural language',
  btnVoice: 'Voice',
  placeholderText: 'I need ₹1.2 lakh for a tailoring shop. My family earns ₹1.5 lakh a year.',
  voiceListening: 'Listening…',
  voiceSpeak: 'Speak naturally',
  voiceDescListening: 'We’ll add your words to the request.',
  voiceDescSpeak: 'Use the microphone, then review the transcript.',
  btnStop: 'Stop',
  btnStart: 'Start recording',
  placeholderTranscript: 'Your transcript will appear here...',
  labelLoanAmount: 'Loan amount',
  labelUnit: 'Unit',
  labelAnnualIncome: 'Annual income',
  labelPurpose: 'Purpose',
  unitLakh: 'Lakh',
  unitCrore: 'Crore',
  unitThousand: 'Thousand',
  unitRupees: 'Rupees',
  purposeGeneral: 'General',
  purposeTailoring: 'Tailoring',
  purposeDairy: 'Dairy',
  purposeWelding: 'Welding',
  purposeFarming: 'Farming',
  purposeEducation: 'Education',
  labelUnderstanding: 'Understanding',
  labelRequirement: 'requirement',
  labelAddRequirement: 'Add requirement',
  labelIncome: 'income',
  labelAddIncome: 'Add income',
  labelTryExample: 'Try an example',
  btnAnalysing: 'Analysing profile…',
  btnAnalyse: 'Analyse eligibility',
  eyebrowAssessment: 'Assessment',
  titleOutlook: 'Your financial outlook',
  titleResultsPlaceholder: 'Results will appear here',
  btnNewAssessment: 'New assessment',
  descPlaceholderResults: 'Your eligibility result, suggested financial terms and support partners will appear after analysis.',
  eyebrowOutcome: 'Eligibility outcome',
  loanConcessional: 'Concessional loan',
  noteVerification: 'Subject to final verification',
  fallbackReason: 'Based on your current inputs, these are the financial terms for consideration.',
  eyebrowTerms: 'Key financial terms',
  labelProjectCost: 'Project cost',
  labelInterestRate: 'Interest rate',
  labelMargin: 'Beneficiary margin',
  labelMoratorium: 'Moratorium',
  labelMonths: 'months',
  eyebrowEmi: 'EMI estimate',
  perMonth: '/ month',
  labelInterest: 'Interest',
  labelTenure: 'Tenure',
  labelPrincipal: 'Principal',
  moratoriumNoteActive: 'moratorium before standard EMI begins.',
  moratoriumNoteNone: 'No moratorium applied.',
  eyebrowGuidance: 'Application guidance',
  titlePartners: 'Nearby support partners',
  kmAway: 'km away',
  capacityAvailable: 'allocation available',
  directions: 'Open directions',
  mapTitle: 'Your location and nearby routing area',
  healthy: 'Healthy',
  pending: 'Pending',
  emptyPartners: 'No partners are available for this result yet. You can still use the assessment above to prepare your application.',
  voiceUnsupported: 'Voice input is not supported in this browser. Please use text or structured profile.',
  voiceUnavailable: 'Voice capture is unavailable for {language} in this browser. Please type your request instead.',
  requestRequired: 'Please tell us what you need support for.',
  serviceUnavailable: 'The service is currently unavailable.',
  translating: 'Translating UI…',
  assessmentComplete: 'Assessment complete'
}

const activeTab = ref('text')
const selectedLanguage = ref(languages[0])
const uiTexts = computed(() => getStaticTexts(selectedLanguage.value.code, defaultTexts))
const demoTexts = computed(() => getStaticDemos(selectedLanguage.value.code, initialDemoTexts))
const userLocation = ref({ latitude: 22.9734, longitude: 78.6569, label: 'Default location — use your location for accurate results' })
const locating = ref(false)
const greetings = {
  en: ['Good night.', 'Good morning.', 'Good afternoon.', 'Good evening.'],
  hi: ['शुभ रात्रि।', 'सुप्रभात।', 'नमस्कार।', 'शुभ संध्या।'],
  bn: ['শুভ রাত্রি।', 'সুপ্রভাত।', 'শুভ অপরাহ্ণ।', 'শুভ সন্ধ্যা।'],
  te: ['శుభ రాత్రి.', 'శుభోదయం.', 'శుభ మధ్యాహ్నం.', 'శుభ సాయంత్రం.'],
  mr: ['शुभ रात्री.', 'शुभ सकाळ.', 'शुभ दुपार.', 'शुभ संध्याकाळ.'],
  ta: ['இனிய இரவு.', 'காலை வணக்கம்.', 'மதிய வணக்கம்.', 'மாலை வணக்கம்.']
}
const currentTime = ref(Date.now())
const currentGreeting = computed(() => {
  currentTime.value
  const hour = new Date().getHours()
  const period = hour < 5 ? 0 : hour < 12 ? 1 : hour < 17 ? 2 : hour < 21 ? 3 : 0
  return greetings[selectedLanguage.value.code][period]
})
const greetingTimer = window.setInterval(() => { currentTime.value = Date.now() }, 60000)
const inputText = ref(demoTexts.value[0].text)
const results = ref(null)
const rawResults = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
const isListening = ref(false)
const recognition = ref(null)

watch(selectedLanguage, (language, previousLanguage) => {
  const previousDemos = getStaticDemos(previousLanguage?.code || 'en', initialDemoTexts)
  const demoIndex = previousDemos.findIndex(demo => demo.text === inputText.value)
  if (demoIndex >= 0) inputText.value = getStaticDemos(language.code, initialDemoTexts)[demoIndex].text
})

const formData = ref({ amount: '3', unit: 'lakh', annualIncome: '300000', loanType: 'General' })
const emiInputs = ref({ principal: 0, rate: 7.5, tenure: 36, moratorium: 6 })
const hasResults = computed(() => Boolean(results.value?.simulation))
const mapUrl = computed(() => {
  const { latitude, longitude } = userLocation.value
  const delta = 0.08
  return `https://www.openstreetmap.org/export/embed.html?bbox=${longitude - delta}%2C${latitude - delta}%2C${longitude + delta}%2C${latitude + delta}&layer=mapnik&marker=${latitude}%2C${longitude}`
})

const useCurrentLocation = () => {
  if (!navigator.geolocation) {
    errorMessage.value = 'Location is not supported in this browser. You can continue with the demo location.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      userLocation.value = { latitude: Number(coords.latitude.toFixed(6)), longitude: Number(coords.longitude.toFixed(6)), label: 'Using your current location' }
      locating.value = false
    },
    () => {
      errorMessage.value = 'We could not access your location. The demo location is still selected.'
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

const translateResult = async result => {
  if (!result || selectedLanguage.value.code === 'en') return
  const texts = {
    scheme_category: result.simulation.scheme_category || '',
    rejection_reason: result.simulation.rejection_reason || '',
    ...Object.fromEntries(result.recommended_partners.map((partner, index) => [`partner_type_${index}`, partner.type]))
  }
  const response = await axios.post(`${API_BASE_URL}/translate`, {
    texts,
    target_language: selectedLanguage.value.code,
    source_language: 'en'
  })
  const translations = response.data.translations || {}
  results.value = {
    ...result,
    simulation: {
      ...result.simulation,
      scheme_category: translations.scheme_category || result.simulation.scheme_category,
      rejection_reason: translations.rejection_reason || result.simulation.rejection_reason
    },
    recommended_partners: result.recommended_partners.map((partner, index) => ({
      ...partner,
      type: translations[`partner_type_${index}`] || partner.type
    }))
  }
}

const currency = (value, compact = false) => {
  const number = Number(value) || 0
  if (compact) {
    if (number >= 10000000) return `₹${(number / 10000000).toFixed(1).replace(/\.0$/, '')}Cr`
    if (number >= 100000) return `₹${(number / 100000).toFixed(1).replace(/\.0$/, '')}L`
    if (number >= 1000) return `₹${(number / 1000).toFixed(1).replace(/\.0$/, '')}K`
  }
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(number)
}

const profileSummary = computed(() => {
  if (activeTab.value === 'form') {
    const mult = { lakh: 100000, crore: 10000000, thousand: 1000, rupees: 1 }[formData.value.unit] || 1
    return { sector: formData.value.loanType, amount: Number(formData.value.amount) * mult, income: Number(formData.value.annualIncome) }
  }
  const text = inputText.value.toLowerCase()
  const sectors = ['tailoring', 'dairy', 'welding', 'farming', 'education', 'engineering']
  const match = sectors.find(s => text.includes(s)) || 'General'
  const lakh = text.match(/([\d.]+)\s*lakh/)
  const income = text.match(/(?:earns?|income(?: is)?|family earns)\s*(?:₹|rs\.?|rupees?)?\s*([\d,]+)/)
  return {
    sector: match === 'engineering' ? 'Education' : match[0].toUpperCase() + match.slice(1),
    amount: lakh ? Number(lakh[1]) * 100000 : 0,
    income: income ? Number(income[1].replace(/,/g, '')) : 0
  }
})

const displaySector = computed(() => {
  const purposeKeys = {
    General: 'purposeGeneral',
    Tailoring: 'purposeTailoring',
    Dairy: 'purposeDairy',
    Welding: 'purposeWelding',
    Farming: 'purposeFarming',
    Education: 'purposeEducation'
  }
  return uiTexts.value[purposeKeys[profileSummary.value.sector]] || profileSummary.value.sector
})

const emiSummary = computed(() => {
  const p = Number(emiInputs.value.principal) || 0
  const r = Number(emiInputs.value.rate) / 1200 || 0
  const t = Number(emiInputs.value.tenure) || 1
  const emi = r ? (p * r * Math.pow(1 + r, t)) / (Math.pow(1 + r, t) - 1) : p / t
  const payable = emi * t
  return { principal: p, emi, totalInterest: payable - p, moratorium: Number(emiInputs.value.moratorium) || 0 }
})

const interestWidth = computed(() => emiSummary.value.principal + emiSummary.value.totalInterest ? Math.max(0, (emiSummary.value.totalInterest / (emiSummary.value.principal + emiSummary.value.totalInterest)) * 100) : 0)

watch(results, value => {
  if (value?.simulation) {
    emiInputs.value = {
      principal: Number(value.simulation.concessional_loan_amount || 0),
      rate: Number(value.simulation.interest_rate || 7.5),
      tenure: 36,
      moratorium: Number(value.simulation.moratorium_months || 6)
    }
  }
})

const resetResultState = () => { results.value = null; rawResults.value = null; errorMessage.value = '' }
const useDemoInput = demo => { activeTab.value = 'text'; inputText.value = demo.text; resetResultState() }
const buildFormText = () => formData.value.loanType === 'Education' ? `I need ${formData.value.amount} ${formData.value.unit} for my education loan. I am a student. My annual income is ${formData.value.annualIncome} rupees.` : `I need ${formData.value.amount} ${formData.value.unit} for my ${formData.value.loanType.toLowerCase()} business. My annual income is ${formData.value.annualIncome} rupees.`

const startVoiceCapture = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    errorMessage.value = uiTexts.value.voiceUnsupported
    return
  }
  recognition.value?.stop()
  const instance = new SpeechRecognition()
  instance.lang = selectedLanguage.value.voiceCode
  instance.interimResults = false
  instance.maxAlternatives = 1
  instance.onstart = () => { isListening.value = true; errorMessage.value = '' }
  instance.onresult = e => { inputText.value = e.results[0][0].transcript; activeTab.value = 'voice'; resetResultState() }
  instance.onerror = () => { errorMessage.value = uiTexts.value.voiceUnavailable.replace('{language}', selectedLanguage.value.label) }
  instance.onend = () => { isListening.value = false }
  recognition.value = instance
  instance.start()
}

const stopVoiceCapture = () => { recognition.value?.stop(); isListening.value = false }

const submitApplication = async () => {
  const text = activeTab.value === 'form' ? buildFormText() : inputText.value
  if (!text.trim()) {
    errorMessage.value = uiTexts.value.requestRequired
    return
  }
  isLoading.value = true
  errorMessage.value = ''
  try {
    const payload = activeTab.value === 'form' ? {
      input_mode: 'form',
      loan_type: formData.value.loanType,
      capital_required: profileSummary.value.amount,
      annual_income: profileSummary.value.income,
      latitude: userLocation.value.latitude,
      longitude: userLocation.value.longitude,
      language: selectedLanguage.value.code
    } : {
      input_mode: activeTab.value,
      translated_text: text,
      latitude: userLocation.value.latitude,
      longitude: userLocation.value.longitude,
      language: selectedLanguage.value.code
    }
    const response = await axios.post(`${API_BASE_URL}/apply`, payload)
    rawResults.value = response.data?.data || response.data
    if (!rawResults.value?.simulation) throw new Error('The server returned an incomplete assessment.')
    results.value = rawResults.value
    if (selectedLanguage.value.code !== 'en') await translateResult(rawResults.value)
  } catch (error) {
    errorMessage.value = `${uiTexts.value.serviceUnavailable} ${error?.response?.data?.detail || error?.message || ''}`.trim()
  } finally {
    isLoading.value = false
  }
}

const handleAnalyze = () => {
  submitApplication()
}

onBeforeUnmount(() => { stopVoiceCapture(); window.clearInterval(greetingTimer) })
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#top"><span class="brand-mark"><img :src="rinudayIcon" alt="" width="20" height="20" /></span><span>Rinuday</span></a>
      <p class="brand-subtitle">{{ uiTexts.brandSubtitle }}</p>
      <div class="header-tools">
        <label class="language-picker">
          <Languages :size="16" />
          <select v-model="selectedLanguage">
            <option v-for="language in languages" :key="language.code" :value="language" :disabled="language.supported === false">
              {{ language.native }} · {{ language.label }}
            </option>
          </select>
        </label>
        <span class="location"><MapPin :size="15" /> {{ uiTexts.location }}</span>
        <span class="avatar">R</span>
      </div>
    </header>
    <main id="top" class="workspace">
      <section class="intro-row">
        <div>
          <p class="eyebrow">{{ uiTexts.eyebrowWorkspace }}</p>
          <h1>{{ currentGreeting }}<br><span>{{ uiTexts.headingMain2 }}</span></h1>
        </div>
        <p class="intro-copy">{{ uiTexts.introCopy }}</p>
      </section>
      <section class="metrics">
        <div class="metric"><span>{{ uiTexts.metricRequired }}</span><strong>{{ profileSummary.amount ? currency(profileSummary.amount, true) : '—' }}</strong></div>
        <div class="metric"><span>{{ uiTexts.metricIncome }}</span><strong>{{ profileSummary.income ? currency(profileSummary.income, true) : '—' }}</strong></div>
        <div class="metric"><span>{{ uiTexts.metricSector }}</span><strong>{{ displaySector }}</strong></div>
        <div class="metric metric-status">
          <span>{{ uiTexts.metricStatus }}</span>
          <strong>{{ results?.simulation ? (results.simulation.is_eligible ? uiTexts.statusEligible : uiTexts.statusReview) : uiTexts.statusReady }}</strong>
        </div>
      </section>
      <section class="dashboard-grid">
        <article class="input-panel">
          <div class="location-control">
            <span><MapPin :size="14" /> {{ userLocation.label }}</span>
            <button type="button" @click="useCurrentLocation" :disabled="locating">{{ locating ? 'Locating...' : 'Use my location' }}</button>
          </div>
          <div class="panel-heading">
            <div>
              <p class="eyebrow">{{ uiTexts.eyebrowSupport }}</p>
              <h2>{{ uiTexts.titleLookingFor }}</h2>
            </div>
            <button class="mode-link" :class="{active: activeTab === 'form'}" type="button" @click="activeTab = 'form'">
              <SlidersHorizontal :size="15" /> {{ uiTexts.btnStructured }}
            </button>
          </div>
          <div class="input-mode-bar">
            <button :class="{active: activeTab === 'text'}" type="button" @click="activeTab = 'text'">{{ uiTexts.btnNatural }}</button>
            <button :class="{active: activeTab === 'voice'}" type="button" @click="activeTab = 'voice'"><Mic :size="14" /> {{ uiTexts.btnVoice }}</button>
          </div>
          <textarea v-if="activeTab === 'text'" v-model="inputText" rows="6" :placeholder="uiTexts.placeholderText"></textarea>
          <div v-else-if="activeTab === 'voice'" class="voice-stage">
            <button class="mic-button" :class="{listening: isListening}" type="button" @click="isListening ? stopVoiceCapture() : startVoiceCapture()"><Volume2 :size="21" /></button>
            <div>
              <strong>{{ isListening ? uiTexts.voiceListening : uiTexts.voiceSpeak }}</strong>
              <p>{{ isListening ? uiTexts.voiceDescListening : uiTexts.voiceDescSpeak }}</p>
            </div>
            <button class="text-button" type="button" @click="isListening ? stopVoiceCapture() : startVoiceCapture()">
              {{ isListening ? uiTexts.btnStop : uiTexts.btnStart }}
            </button>
            <textarea v-model="inputText" rows="3" :placeholder="uiTexts.placeholderTranscript"></textarea>
          </div>
          <div v-else class="profile-form">
            <div><label>{{ uiTexts.labelLoanAmount }}</label><input v-model="formData.amount" type="number" min="0"></div>
            <div>
              <label>{{ uiTexts.labelUnit }}</label>
              <select v-model="formData.unit">
                <option value="lakh">{{ uiTexts.unitLakh }}</option>
                <option value="crore">{{ uiTexts.unitCrore }}</option>
                <option value="thousand">{{ uiTexts.unitThousand }}</option>
                <option value="rupees">{{ uiTexts.unitRupees }}</option>
              </select>
            </div>
            <div><label>{{ uiTexts.labelAnnualIncome }}</label><input v-model="formData.annualIncome" type="number" min="0"></div>
            <div>
              <label>{{ uiTexts.labelPurpose }}</label>
              <select v-model="formData.loanType">
                <option value="General">{{ uiTexts.purposeGeneral }}</option>
                <option value="Tailoring">{{ uiTexts.purposeTailoring }}</option>
                <option value="Dairy">{{ uiTexts.purposeDairy }}</option>
                <option value="Welding">{{ uiTexts.purposeWelding }}</option>
                <option value="Farming">{{ uiTexts.purposeFarming }}</option>
                <option value="Education">{{ uiTexts.purposeEducation }}</option>
              </select>
            </div>
          </div>
          <div class="extracted">
            <span>{{ uiTexts.labelUnderstanding }}</span>
            <p>{{ displaySector }} <i /> {{ profileSummary.amount ? `${currency(profileSummary.amount, true)} ${uiTexts.labelRequirement}` : uiTexts.labelAddRequirement }} <i /> {{ profileSummary.income ? `${currency(profileSummary.income, true)} ${uiTexts.labelIncome}` : uiTexts.labelAddIncome }}</p>
          </div>
          <form class="input-footer" @submit.prevent="handleAnalyze">
            <div class="examples">
              <span>{{ uiTexts.labelTryExample }}</span>
              <button v-for="demo in demoTexts" :key="demo.id" type="button" @click="useDemoInput(demo)">{{ demo.label }}</button>
            </div>
            <button class="primary-button" :disabled="isLoading" type="submit">
              {{ isLoading ? uiTexts.btnAnalysing : uiTexts.btnAnalyse }} <ArrowUpRight :size="17" />
            </button>
          </form>
          <p v-if="errorMessage" class="error-message"><CircleAlert :size="16" /> {{ errorMessage }}</p>
        </article>
      </section>
      <section class="results-section">
        <div class="section-title">
          <div>
            <p class="eyebrow">{{ uiTexts.eyebrowAssessment }}</p>
            <h2>{{ hasResults ? uiTexts.titleOutlook : uiTexts.titleResultsPlaceholder }}</h2>
          </div>
          <button v-if="hasResults" class="quiet-action" type="button" @click="resetResultState"><RotateCcw :size="15" /> {{ uiTexts.btnNewAssessment }}</button>
        </div>
        <div v-if="!results" class="results-placeholder">
          <Calculator :size="22" />
          <p>{{ uiTexts.descPlaceholderResults }}</p>
        </div>
        <template v-else-if="hasResults">
          <div class="result-grid">
            <article class="best-match">
              <div>
                <p class="eyebrow">{{ uiTexts.eyebrowOutcome }}</p>
                <p class="result-status" :class="results.simulation.is_eligible ? 'positive' : 'caution'">
                  {{ results.simulation.is_eligible ? uiTexts.statusEligible : uiTexts.statusReview }}
                </p>
                <h3>{{ results.simulation.scheme_category || uiTexts.assessmentComplete }}</h3>
                <p>{{ results.simulation.rejection_reason || uiTexts.fallbackReason }}</p>
              </div>
              <div class="support-amount">
                <span>{{ uiTexts.loanConcessional }}</span>
                <strong>{{ currency(results.simulation.concessional_loan_amount) }}</strong>
                <small>{{ uiTexts.noteVerification }}</small>
              </div>
            </article>
            <article class="terms-card">
              <p class="eyebrow">{{ uiTexts.eyebrowTerms }}</p>
              <div class="term-list">
                <div><span>{{ uiTexts.labelProjectCost }}</span><strong>{{ currency(results.simulation.total_project_cost) }}</strong></div>
                <div><span>{{ uiTexts.labelInterestRate }}</span><strong>{{ results.simulation.interest_rate ?? '—' }}%</strong></div>
                <div><span>{{ uiTexts.labelMargin }}</span><strong>{{ currency(results.simulation.beneficiary_margin_money) }}</strong></div>
                <div><span>{{ uiTexts.labelMoratorium }}</span><strong>{{ results.simulation.moratorium_months ?? '—' }} {{ uiTexts.labelMonths }}</strong></div>
              </div>
            </article>
          </div>
          <div class="lower-grid">
            <article class="emi-card">
              <div class="panel-heading">
                <div>
                  <p class="eyebrow">{{ uiTexts.eyebrowEmi }}</p>
                  <h3>{{ currency(emiSummary.emi) }} <span>{{ uiTexts.perMonth }}</span></h3>
                </div>
                <Calculator :size="19" class="accent-icon" />
              </div>
              <div class="emi-fields">
                <label>{{ uiTexts.labelLoanAmount }}<input v-model.number="emiInputs.principal" type="number" min="0"></label>
                <label>{{ uiTexts.labelInterest }}<input v-model.number="emiInputs.rate" type="number" min="0" step="0.1"></label>
                <label>{{ uiTexts.labelTenure }}<input v-model.number="emiInputs.tenure" type="number" min="1"></label>
              </div>
              <div class="repayment-bar">
                <div class="principal-bar" :style="{width: `${100 - interestWidth}%`}"></div>
                <div class="interest-bar" :style="{width: `${interestWidth}%`}"></div>
              </div>
              <div class="bar-legend">
                <span><i class="principal-dot"></i>{{ uiTexts.labelPrincipal }} {{ currency(emiSummary.principal) }}</span>
                <span><i class="interest-dot"></i>{{ uiTexts.labelInterest }} {{ currency(emiSummary.totalInterest) }}</span>
              </div>
              <p class="moratorium-note">{{ emiSummary.moratorium ? `${emiSummary.moratorium}-${uiTexts.labelMonths} ${uiTexts.moratoriumNoteActive}` : uiTexts.moratoriumNoteNone }}</p>
            </article>
            <article class="partners-card">
              <div class="panel-heading">
                <div>
                  <p class="eyebrow">{{ uiTexts.eyebrowGuidance }}</p>
                  <h3>{{ uiTexts.titlePartners }}</h3>
                </div>
                <span class="partner-count">{{ results.recommended_partners.length }}</span>
              </div>
              <div v-if="results.recommended_partners.length" class="partner-list">
                <div v-for="partner in results.recommended_partners" :key="partner.partner_id" class="partner">
                  <div class="partner-logo">{{ partner.name.slice(0, 1) }}</div>
                  <div>
                    <strong>{{ partner.name }}</strong>
                    <p>{{ partner.type }} · {{ partner.distance_km }} {{ uiTexts.kmAway }} · ₹{{ currency(partner.remaining_capacity, true) }} {{ uiTexts.capacityAvailable }}</p>
                  </div>
                  <span :class="partner.health_status === 'Healthy' ? 'healthy' : 'pending'">
                    {{ partner.health_status === 'Healthy' ? uiTexts.healthy : uiTexts.pending }}
                  </span>
                  <a :href="`https://www.google.com/maps/dir/?api=1&destination=${partner.latitude},${partner.longitude}`" target="_blank" rel="noreferrer">{{ uiTexts.directions }}</a>
                </div>
              </div>
              <p v-else class="empty-state">{{ uiTexts.emptyPartners }}</p>
            </article>
          </div>
          <div class="map-panel">
            <div class="map-heading">{{ uiTexts.mapTitle }}</div>
            <iframe :src="mapUrl" title="Applicant location map" loading="lazy"></iframe>
          </div>
        </template>
      </section>
    </main>
  </div>
</template>
