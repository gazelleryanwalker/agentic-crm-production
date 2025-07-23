const express = require('express');
const serverless = require('serverless-http');

const app = express();
const router = express.Router();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// Health check
router.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    message: 'Agentic CRM API is running',
    timestamp: new Date().toISOString()
  });
});

// Authentication endpoints
router.post('/auth/login', (req, res) => {
  const { username, password } = req.body;
  
  // Simple authentication for demo
  if (username === 'admin' && password === 'admin123') {
    res.json({
      success: true,
      token: 'demo-jwt-token-' + Date.now(),
      user: {
        id: 1,
        username: 'admin',
        email: 'admin@agenticcrm.com',
        first_name: 'System',
        last_name: 'Administrator',
        is_admin: true
      }
    });
  } else {
    res.status(401).json({
      success: false,
      message: 'Invalid credentials'
    });
  }
});

// Dashboard data
router.get('/dashboard/stats', (req, res) => {
  res.json({
    total_contacts: 42,
    active_deals: 8,
    pending_tasks: 15,
    revenue_this_month: 25000,
    conversion_rate: 0.18,
    ai_insights: [
      "Your conversion rate has improved 12% this month",
      "3 high-value deals are likely to close this week",
      "Contact follow-up automation saved 8 hours this week"
    ]
  });
});

// Contacts endpoints
router.get('/crm/contacts', (req, res) => {
  res.json({
    contacts: [
      {
        id: 1,
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
        company: 'Tech Corp',
        lead_status: 'qualified',
        lead_score: 85
      },
      {
        id: 2,
        first_name: 'Jane',
        last_name: 'Smith',
        email: 'jane.smith@example.com',
        company: 'Innovation Inc',
        lead_status: 'new',
        lead_score: 72
      }
    ]
  });
});

// Deals endpoints
router.get('/crm/deals', (req, res) => {
  res.json({
    deals: [
      {
        id: 1,
        title: 'Enterprise Software License',
        value: 50000,
        stage: 'negotiation',
        probability: 0.8,
        close_date: '2025-08-15'
      },
      {
        id: 2,
        title: 'Consulting Services',
        value: 25000,
        stage: 'proposal',
        probability: 0.6,
        close_date: '2025-08-30'
      }
    ]
  });
});

// AI Assistant endpoint
router.post('/ai/chat', (req, res) => {
  const { message } = req.body;
  
  // Simple AI response for demo
  const responses = [
    "I can help you analyze your customer data and provide insights.",
    "Based on your recent activity, I recommend following up with 3 high-priority leads.",
    "Your sales pipeline shows strong momentum this quarter.",
    "I've identified potential upsell opportunities with existing clients."
  ];
  
  const randomResponse = responses[Math.floor(Math.random() * responses.length)];
  
  res.json({
    response: randomResponse,
    timestamp: new Date().toISOString()
  });
});

// Memory search endpoint
router.post('/memory/search', (req, res) => {
  const { query } = req.body;
  
  res.json({
    results: [
      {
        content: `Found relevant information about: ${query}`,
        type: 'contact',
        relevance: 0.95,
        timestamp: new Date().toISOString()
      }
    ]
  });
});

app.use('/api', router);

module.exports.handler = serverless(app);
