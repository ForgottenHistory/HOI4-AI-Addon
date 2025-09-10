use std::collections::HashMap;
use std::fs::File;
use std::io::Write;
use std::env;
use hoi4save::{Hoi4File, PdsDate};
use serde_json;

mod enhanced_country;
use enhanced_country::{EnhancedHoi4Save, DatabaseCharacter};

use std::collections::BTreeMap;
use regex::Regex;

fn extract_completed_focuses(save_content: &str) -> BTreeMap<String, Vec<String>> {
    let mut completed_by_country = BTreeMap::new();
    
    // Look for the unique pattern: TAG={\n\t\tinstances_counter=
    // This guarantees we're in the actual country section
    let country_pattern = Regex::new(r"(?m)^\t([A-Z]{3})=\{\n\t\tinstances_counter=").unwrap();
    let completed_regex = Regex::new(r#"completed="([^"]+)""#).unwrap();
    
    // Find all country sections with this unique pattern
    let mut country_matches: Vec<(String, usize)> = Vec::new();
    for cap in country_pattern.captures_iter(save_content) {
        let tag = cap[1].to_string();
        let pos = cap.get(0).unwrap().start();
        country_matches.push((tag, pos));
    }
    
    println!("Found {} countries with instances_counter pattern", country_matches.len());
    
    // Process each country
    for i in 0..country_matches.len() {
        let (country_tag, start_pos) = &country_matches[i];
        
        // Find where this country's section starts (at the TAG={ part)
        let country_def_start = start_pos + 1; // Skip the initial tab
        
        // Find the end of this country's section
        // Start after "TAG={"
        let search_start = country_def_start + country_tag.len() + 2;
        
        // Count braces to find the end of this country's data
        let mut brace_count = 1;
        let mut country_end = search_start;
        
        for (idx, ch) in save_content[search_start..].char_indices() {
            if ch == '{' {
                brace_count += 1;
            } else if ch == '}' {
                brace_count -= 1;
                if brace_count == 0 {
                    country_end = search_start + idx;
                    break;
                }
            }
        }
        
        // Extract this country's entire section
        let country_section = &save_content[country_def_start..country_end];
        
        // Look for focus block within this country's section
        if let Some(focus_start) = country_section.find("\t\tfocus={") {
            // Find the matching closing brace for the focus block
            let focus_content_start = focus_start + 9; // Skip "\t\tfocus={"
            let mut brace_count = 1;
            let mut focus_end = focus_content_start;
            
            for (idx, ch) in country_section[focus_content_start..].char_indices() {
                if ch == '{' {
                    brace_count += 1;
                } else if ch == '}' {
                    brace_count -= 1;
                    if brace_count == 0 {
                        focus_end = focus_content_start + idx;
                        break;
                    }
                }
            }
            
            // Extract completed focuses from this country's focus block
            let focus_content = &country_section[focus_content_start..focus_end];
            let mut completed_focuses = Vec::new();
            
            for completed_cap in completed_regex.captures_iter(focus_content) {
                completed_focuses.push(completed_cap[1].to_string());
            }
            
            if !completed_focuses.is_empty() {
                println!("  {} has {} completed focuses: {:?}", 
                    country_tag, completed_focuses.len(), &completed_focuses);
                completed_by_country.insert(country_tag.clone(), completed_focuses);
            } else if focus_content.contains("completed") {
                println!("  {} has 'completed' in focus but regex didn't match", country_tag);
                // Show a sample for debugging
                if let Some(idx) = focus_content.find("completed") {
                    let sample_start = idx.saturating_sub(20);
                    let sample_end = (idx + 50).min(focus_content.len());
                    println!("    Sample: {:?}", &focus_content[sample_start..sample_end]);
                }
            }
        } else {
            // Try without tabs in case formatting varies
            if country_section.contains("focus={") {
                println!("  {} has focus block but not with expected tab formatting", country_tag);
            }
        }
    }
    
    println!("Total countries with completed focuses: {}", completed_by_country.len());
    
    completed_by_country
}

fn extract_character_names(save_content: &str) -> HashMap<i32, String> {
    let mut character_names = HashMap::new();
    
    // Look for character database entries
    let character_pattern = Regex::new(r#"character=\{\s*id=\{\s*id=(\d+)\s+type=\d+\s*\}\s*[^}]*?name="([^"]+)""#).unwrap();
    
    for cap in character_pattern.captures_iter(save_content) {
        if let Ok(id) = cap[1].parse::<i32>() {
            let name = cap[2].to_string();
            println!("Found character: ID {} -> {}", id, name);
            character_names.insert(id, name);
        }
    }
    
    println!("Extracted {} character names", character_names.len());
    character_names
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    let save_path = if args.len() > 1 {
        &args[1]
    } else {
        "autosave.hoi4"
    };
    
    let output_path = if args.len() > 2 {
        &args[2]
    } else {
        "../data/game_data.json"
    };
    
    println!("Parsing HOI4 save file: {}", save_path);
    
    if !std::path::Path::new(save_path).exists() {
        println!("Error: Save file '{}' not found!", save_path);
        return Ok(());
    }
    
    let data = std::fs::read(save_path)?;
    let save_content = String::from_utf8_lossy(&data);
    
    // Extract completed focuses before main parsing
    println!("Extracting completed focuses...");
    let completed_focuses = extract_completed_focuses(&save_content);
    
    // Extract character names
    println!("Extracting character names...");
    let character_names = extract_character_names(&save_content);
    
    let save_file = Hoi4File::from_slice(&data)?;
    let resolver = HashMap::<u16, &str>::new();
    println!("Attempting to parse save file...");
    let save: EnhancedHoi4Save = save_file.parse(resolver)?;
    
    println!("Player country: {}", save.player);
    println!("Date: {}", save.date.game_fmt());
    println!("Total countries: {}", save.countries.len());
    
    // Filter out "id" and "=" tokens from events
    let clean_events: Vec<&String> = save.fired_event_names.iter()
        .filter(|event| *event != "id" && *event != "=")
        .collect();
    
    // Filter for active countries (not default values and can actually do focuses)
    let active_countries: Vec<_> = save.countries.iter()
        .filter(|(_, country)| {
            // Must have non-default stability/war_support values
            let has_activity = country.stability != 0.5 || country.war_support != 0.5;
            
            // Must have either a current focus or be able to do focuses (not just have focus=null)
            let can_do_focuses = match &country.focus {
                Some(focus) => {
                    // If current is Some (has a focus) or current is None but progress exists (just finished)
                    focus.current.is_some() || focus.progress.is_some()
                },
                None => false, // No focus system at all means inactive country
            };
            
            has_activity && can_do_focuses
        })
        .collect();
    
    // Create output structure
    let output_data = serde_json::json!({
        "metadata": {
            "player": save.player,
            "date": save.date.game_fmt().to_string(),
            "total_countries": save.countries.len(),
            "active_countries": active_countries.len()
        },
        "events": clean_events,
        "countries": active_countries.iter().map(|(tag, country)| {
            let mut country_data = serde_json::to_value(country).unwrap();
            
            // Inject completed focuses if they exist
            if let Some(completed) = completed_focuses.get(tag.as_str()) {
                if let Some(focus) = country_data.get_mut("focus") {
                    focus["completed"] = serde_json::json!(completed);
                }
            }
            
            // Enrich character data with names
            if let Some(politics) = country_data.get_mut("politics") {
                if let Some(parties) = politics.get_mut("parties") {
                    for (_, party) in parties.as_object_mut().unwrap() {
                        if let Some(country_leaders) = party.get_mut("country_leader") {
                            if let Some(leaders_array) = country_leaders.as_array_mut() {
                                for leader in leaders_array {
                                    if let Some(character) = leader.get_mut("character") {
                                        if let Some(id) = character.get("id").and_then(|id| id.as_i64()) {
                                            if let Some(name) = character_names.get(&(id as i32)) {
                                                character.as_object_mut().unwrap().insert("name".to_string(), serde_json::json!(name));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            serde_json::json!({
                "tag": tag.as_str(),
                "data": country_data
            })
        }).collect::<Vec<_>>()
    });
    
    // Write JSON to file
    let mut file = File::create(output_path)?;
    file.write_all(serde_json::to_string_pretty(&output_data)?.as_bytes())?;
    
    println!("Data extracted to: {}", output_path);
    println!("Events: {}", clean_events.len());
    println!("Active countries: {}", active_countries.len());
    
    Ok(())
}