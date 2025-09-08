use std::collections::HashMap;
use std::fs::File;
use std::io::Write;
use hoi4save::{Hoi4File, PdsDate};
use serde_json;

mod enhanced_country;
use enhanced_country::{EnhancedHoi4Save};

use std::collections::BTreeMap;
use regex::Regex;

fn extract_completed_focuses(save_content: &str) -> BTreeMap<String, Vec<String>> {
    let mut completed_by_country = BTreeMap::new();
    
    // Regex to find country sections and their completed focuses
    let country_regex = Regex::new(r"([A-Z]{3})=\{[\s\S]*?focus=\{([\s\S]*?)\}").unwrap();
    let completed_regex = Regex::new(r#"completed="([^"]+)""#).unwrap();
    
    for country_cap in country_regex.captures_iter(save_content) {
        let country_tag = country_cap[1].to_string();
        let focus_section = &country_cap[2];
        
        let mut completed_focuses = Vec::new();
        for completed_cap in completed_regex.captures_iter(focus_section) {
            completed_focuses.push(completed_cap[1].to_string());
        }
        
        if !completed_focuses.is_empty() {
            completed_by_country.insert(country_tag, completed_focuses);
        }
    }
    
    completed_by_country
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let save_path = "autosave.hoi4";
    let output_path = "game_data.json";
    
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
    
    // Filter for active countries (not default 50%/50% values)
    let active_countries: Vec<_> = save.countries.iter()
        .filter(|(_, country)| {
            country.stability != 0.5 || 
            country.war_support != 0.5
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