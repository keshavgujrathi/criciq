import json
import os
import time
from dotenv import load_dotenv
from engine.prompt_loader import load_prompt, fill_template, list_prompt_versions
from engine.llm_client import GroqClient
from engine.validator import run_full_validation, check_consistency

load_dotenv()


def run_eval(test_cases_path: str, results_path: str):
    """
    Run comprehensive evaluation on test cases.
    
    Args:
        test_cases_path: Path to test cases JSON file
        results_path: Path to write results JSON file
    """
    # Load test cases
    with open(test_cases_path, 'r') as f:
        test_cases = json.load(f)
    
    # Initialize LLM client
    llm_client = GroqClient(os.getenv("GROQ_API_KEY"))
    
    results = []
    
    print(f"Running evaluation on {len(test_cases)} test cases...\n")
    print(f"{'Test ID':<8} {'Mode':<15} {'Compliant':<10} {'Halluc':<10} {'Consistent':<10} {'Response Time':<12}")
    print("-" * 75)
    
    for test_case in test_cases:
        test_id = test_case["id"]
        match_title = test_case["match_title"]
        
        # Prepare context text for hallucination checking
        context_text = f"{test_case['context_str']}\n{test_case['scorecard_str']}\n{test_case['commentary_str']}"
        
        for mode in test_case["modes_to_test"]:
            try:
                # Get latest prompt version
                versions = list_prompt_versions(mode)
                if not versions:
                    print(f"❌ No versions found for mode: {mode}")
                    continue
                
                latest_version = versions[-1]
                prompt = load_prompt(mode, latest_version)
                
                # Fill template
                prompt_data = {
                    'match_title': test_case['match_title'],
                    'context_str': test_case['context_str'],
                    'scorecard_str': test_case['scorecard_str'],
                    'commentary_str': test_case['commentary_str']
                }
                
                system_prompt, user_prompt = fill_template(prompt, **prompt_data)
                
                # Run main response
                start_time = time.time()
                response = llm_client.complete(
                    system_prompt, user_prompt, 
                    prompt['model'], prompt['temperature']
                )
                response_time = (time.time() - start_time) * 1000
                
                # Run validation
                validation_result = run_full_validation(response, context_text, mode)
                
                # Run consistency check (2 additional runs)
                consistency_responses = [response]
                for i in range(2):
                    time.sleep(2)  # Rate limiting
                    additional_response = llm_client.complete(
                        system_prompt, user_prompt,
                        prompt['model'], prompt['temperature']
                    )
                    consistency_responses.append(additional_response)
                
                consistency_result = check_consistency(consistency_responses)
                
                # Build result entry
                result = {
                    "test_case_id": test_id,
                    "match_title": match_title,
                    "mode": mode,
                    "prompt_version": latest_version,
                    "response_time_ms": round(response_time, 0),
                    "format_compliant": validation_result["compliant"],
                    "missing_sections": validation_result["missing"],
                    "hallucination_risk": validation_result["risk_flag"],
                    "ungrounded_numbers": validation_result["numbers_ungrounded"],
                    "structurally_consistent": consistency_result["structurally_consistent"],
                    "response_preview": response[:200] + "..." if len(response) > 200 else response
                }
                results.append(result)
                
                # Print summary line
                compliant_check = "✓" if validation_result["compliant"] else "✗"
                halluc_check = "✓" if not validation_result["risk_flag"] else "✗"
                consistent_check = "✓" if consistency_result["structurally_consistent"] else "✗"
                
                print(f"{test_id:<8} {mode:<15} {compliant_check:<10} {halluc_check:<10} {consistent_check:<10} {response_time:.0f} ms")
                
                time.sleep(2)  # Rate limiting between test cases
                
            except Exception as e:
                print(f"❌ Error in {test_id} ({mode}): {str(e)}")
                result = {
                    "test_case_id": test_id,
                    "match_title": match_title,
                    "mode": mode,
                    "error": str(e)
                }
                results.append(result)
    
    # Write results to file
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Evaluation complete. Results written to: {results_path}")
    
    # Print summary statistics
    total_tests = len(results)
    compliant_tests = sum(1 for r in results if r.get("format_compliant", False))
    halluc_safe_tests = sum(1 for r in results if not r.get("hallucination_risk", True))
    consistent_tests = sum(1 for r in results if r.get("structurally_consistent", False))
    
    print(f"\n📊 Summary Statistics:")
    print(f"Total tests: {total_tests}")
    print(f"Format compliant: {compliant_tests}/{total_tests} ({compliant_tests/total_tests*100:.1f}%)")
    print(f"No hallucination risk: {halluc_safe_tests}/{total_tests} ({halluc_safe_tests/total_tests*100:.1f}%)")
    print(f"Structurally consistent: {consistent_tests}/{total_tests} ({consistent_tests/total_tests*100:.1f}%)")


if __name__ == "__main__":
    # Run evaluation
    test_cases_path = "eval/test_cases.json"
    results_path = "results/eval_results.json"
    
    run_eval(test_cases_path, results_path)
