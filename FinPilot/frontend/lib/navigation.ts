import { Calculator, Compass, CreditCard, FileText, FlaskConical, House, Landmark, Settings, SlidersHorizontal, Sparkles, Target } from 'lucide-react';
export const navigation=[
 {name:'Overview',icon:House,description:'Cash flow, spending and your next decision'},
 {name:'Accounts',icon:Landmark,description:'Checking, savings and investment balances'},
 {name:'Transactions',icon:CreditCard,description:'Search the ledger and merchant categories'},
 {name:'Subscriptions',icon:SlidersHorizontal,description:'Review recurring payments and billing schedules'},
 {name:'Goals',icon:Target,description:'House savings, emergency reserve and constraints'},
 {name:'Documents',icon:FileText,description:'Upload and review source documents'},
 {name:'Scenarios',icon:Compass,description:'Model financial changes against your goals'},
 {name:'Tax Planning',icon:Calculator,description:'Reviewed paystubs, federal taxes and contribution scenarios'},
 {name:'FinPilot Copilot',icon:Sparkles,description:'Ask questions with evidence and calculations'},
 {name:'Evaluation Lab',icon:FlaskConical,description:'Run golden questions and inspect measured results'},
 {name:'Settings',icon:Settings,description:'Confirm preferences and review model configuration'},
] as const;
export const searchQuestions=[
 {question:'Can I afford the car in my current loan offer?',keywords:'car loan afford scenario'},
 {question:'How much did I spend last month?',keywords:'spending expenses last month'},
 {question:'Am I withholding enough federal tax?',keywords:'withholding federal tax paycheck'},
 {question:'What is my emergency-fund threshold?',keywords:'emergency fund reserve memory'},
];
