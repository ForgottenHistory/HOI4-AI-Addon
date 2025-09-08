use std::collections::HashMap;
use std::fs::{File, create_dir_all};
use std::io::Write;
use std::path::Path;
use hoi4save::{Hoi4File, PdsDate};

mod enhanced_country;
use enhanced_country::{EnhancedHoi4Save, EnhancedCountry, Politics};

fn write_country_analysis(
    country_tag: &str, 
    country_data: &EnhancedCountry, 
    output_dir: &str
) -> Result<(), Box<dyn std::error::Error>> {
    let filename = format!("{}/{}.txt", output_dir, country_tag);
    let mut file = File::create(&filename)?;
    
    writeln!(file, "=== {} Country Analysis ===", country_tag)?;
    writeln!(file, "Stability: {:.2}%", country_data.stability * 100.0)?;
    writeln!(file, "War Support: {:.2}%", country_data.war_support * 100.0)?;
    writeln!(file, "Variables: {}", country_data.variables.len())?;
    
    if let Some(politics) = &country_data.politics {
        writeln!(file, "\n=== Political Information ===")?;
        
        if let Some(ruling_party) = &politics.ruling_party {
            writeln!(file, "Ruling Party: {}", ruling_party)?;
        }
        
        if let Some(political_power) = politics.political_power {
            writeln!(file, "Political Power: {:.3}", political_power)?;
        }
        
        if let Some(parties) = &politics.parties {
            writeln!(file, "\n=== Party Support ===")?;
            
            if let Some(dem) = &parties.democratic {
                if let Some(pop) = dem.popularity {
                    writeln!(file, "Democratic: {:.1}%", pop)?;
                }
                if let Some(leaders) = &dem.country_leader {
                    for leader in leaders {
                        if let Some(ideology) = &leader.ideology {
                            writeln!(file, "  Leader ideology: {}", ideology)?;
                        }
                        if let Some(character) = &leader.character {
                            if let Some(id) = character.id {
                                writeln!(file, "  Character ID: {}", id)?;
                            }
                        }
                    }
                }
            }
            
            if let Some(com) = &parties.communism {
                if let Some(pop) = com.popularity {
                    writeln!(file, "Communist: {:.1}%", pop)?;
                }
                if let Some(leaders) = &com.country_leader {
                    for leader in leaders {
                        if let Some(ideology) = &leader.ideology {
                            writeln!(file, "  Leader ideology: {}", ideology)?;
                        }
                        if let Some(character) = &leader.character {
                            if let Some(id) = character.id {
                                writeln!(file, "  Character ID: {}", id)?;
                            }
                        }
                    }
                }
            }
            
            if let Some(fas) = &parties.fascism {
                if let Some(pop) = fas.popularity {
                    writeln!(file, "Fascist: {:.1}%", pop)?;
                }
                if let Some(leaders) = &fas.country_leader {
                    for leader in leaders {
                        if let Some(ideology) = &leader.ideology {
                            writeln!(file, "  Leader ideology: {}", ideology)?;
                        }
                        if let Some(character) = &leader.character {
                            if let Some(id) = character.id {
                                writeln!(file, "  Character ID: {}", id)?;
                            }
                        }
                    }
                }
            }
            
            if let Some(neu) = &parties.neutrality {
                if let Some(pop) = neu.popularity {
                    writeln!(file, "Neutrality: {:.1}%", pop)?;
                }
                if let Some(leaders) = &neu.country_leader {
                    for leader in leaders {
                        if let Some(ideology) = &leader.ideology {
                            writeln!(file, "  Leader ideology: {}", ideology)?;
                        }
                        if let Some(character) = &leader.character {
                            if let Some(id) = character.id {
                                writeln!(file, "  Character ID: {}", id)?;
                            }
                        }
                    }
                }
            }
        }
        
        if let Some(ideas) = &politics.ideas {
            writeln!(file, "\n=== National Ideas ===")?;
            for idea in ideas {
                writeln!(file, "- {}", idea)?;
            }
        }
        
        if let Some(last_election) = &politics.last_election {
            writeln!(file, "\nLast Election: {}", last_election)?;
        }
        
        if let Some(elections_allowed) = politics.elections_allowed {
            writeln!(file, "Elections Allowed: {}", elections_allowed)?;
        }
    } else {
        writeln!(file, "\n=== No Political Data Available ===")?;
    }
    
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let save_path = "autosave.hoi4";
    let output_dir = "countries";
    
    println!("Parsing HOI4 save file: {}", save_path);
    
    if !Path::new(save_path).exists() {
        println!("Error: Save file '{}' not found!", save_path);
        return Ok(());
    }
    
    // Create countries directory
    create_dir_all(output_dir)?;
    println!("Created output directory: {}", output_dir);
    
    let data = std::fs::read(save_path)?;
    let save_file = Hoi4File::from_slice(&data)?;
    let resolver = HashMap::<u16, &str>::new();
    let save: EnhancedHoi4Save = save_file.parse(resolver)?;
    
    println!("Player country: {}", save.player);
    println!("Date: {}", save.date.game_fmt());
    println!("Total countries: {}", save.countries.len());
    
    // Filter for active countries (not default 50%/50% values)
    let active_countries: Vec<_> = save.countries.iter()
        .filter(|(_, country)| {
            country.stability != 0.5 || 
            country.war_support != 0.5
        })
        .collect();
    
    println!("Active countries: {}", active_countries.len());
    
    // Process each active country
    let mut countries_with_politics = 0;
    let mut total_processed = 0;
    
    for (country_tag, country_data) in &active_countries {
        let tag_str = country_tag.as_str();
        
        if country_data.politics.is_some() {
            countries_with_politics += 1;
        }
        
        write_country_analysis(tag_str, country_data, output_dir)?;
        total_processed += 1;
        
        if total_processed % 10 == 0 {
            println!("Processed {} countries...", total_processed);
        }
    }
    
    println!("\n=== Analysis Complete ===");
    println!("Processed: {} countries", total_processed);
    println!("Countries with politics data: {}", countries_with_politics);
    println!("Countries with default values (skipped): {}", save.countries.len() - active_countries.len());
    println!("Output directory: {}", output_dir);
    
    // Show some examples
    println!("\nExample files created:");
    for (country_tag, _) in active_countries.iter().take(5) {
        println!("  {}/{}.txt", output_dir, country_tag.as_str());
    }
    
    Ok(())
}