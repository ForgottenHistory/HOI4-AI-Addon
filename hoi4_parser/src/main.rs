use std::collections::HashMap;
use std::fs::File;
use std::io::Write;
use hoi4save::{Hoi4File, PdsDate};
use serde_json;

mod enhanced_country;
use enhanced_country::{EnhancedHoi4Save};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let save_path = "autosave.hoi4";
    let output_path = "game_data.json";
    
    println!("Parsing HOI4 save file: {}", save_path);
    
    if !std::path::Path::new(save_path).exists() {
        println!("Error: Save file '{}' not found!", save_path);
        return Ok(());
    }
    
    let data = std::fs::read(save_path)?;
    let save_file = Hoi4File::from_slice(&data)?;
    let resolver = HashMap::<u16, &str>::new();
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
            serde_json::json!({
                "tag": tag.as_str(),
                "data": country
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