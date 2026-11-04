import type { Scenario } from './types';
export interface TaxProfile {
 tax_year:2026; state:'TX';filing_status:'single'|'married_filing_jointly';as_of:string;employee_keys:string[];
 hsa_coverage:'none'|'self_only'|'family';hsa_eligible_months:number;hsa_eligibility_confirmed:boolean;hsa_payroll_cafeteria_plan_confirmed:boolean;
 other_ordinary_income:string;nonrefundable_credits:string;estimated_payments:string;
 prior_year_total_tax:string|null;prior_year_agi:string|null;prior_year_full_year_return:boolean;
 supported_scope_confirmed:boolean;confirmed:boolean;revision:number;
}
export interface PayrollFacts extends Record<string,string|number|null> {employment_key:string;employee_key:string;employee_name:string;employer_name:string;pay_date:string;remaining_periods:number;annual_periods:number;pay_frequency:string;}
export interface Paystub {id:string;document_id:string;title:string;status:string;facts:PayrollFacts;}
export interface TaxProjection {
 tax_year:number;state:string;rule_version:string;profile_revision:number;as_of:string;filing_status:string;
 figures:Record<string,string>;remaining_paychecks:number;suggested_extra_per_household_paycheck:string|null;safe_harbor_extra_per_household_paycheck:string|null;
 safe_harbor:{annual_screen_passed:boolean|null;required_annual_payment:string|null;current_year_target:string;prior_year_target:string|null;shortfall:string|null;less_than_1000_after_withholding:boolean;note:string};
 workers:{employment_key:string;employee_key:string;employee_name:string;employer_name:string;pay_date:string;annual_periods:number;remaining_periods:number;projected:Record<string,string>;document_id:string;paystub_id:string;current:PayrollFacts}[];
 brackets:{lower_bound:string;upper_bound:string|null;rate:string;taxable_amount:string;tax:string}[];
 sources:{title:string;url:string;section:string}[];assumptions:string[];completeness:string;
}
export interface TaxStrategy {baseline:TaxProjection;alternative:TaxProjection;comparison:Record<string,string>;goal_scenario:Scenario;assumptions:string[];validation:{passed:boolean;checks:string[];errors:string[]};}
export interface PaystubDraft {upload_id:string;document_id:string;fields:Record<string,string|number|null>;evidence:Record<string,{passage:string;label:string;page?:number;section?:string}>;missing_fields:string[];note:string;}
