#!/usr/bin/env ruby

# admin dashboard

require 'sinatra'
require 'json'
require 'sequel'

DB = Sequel.sqlite('dashboard.db')

get '/' do
  redirect '/index.html'
end

get '/data.json' do
  content_type 'application/json'
  sent     = transmitted('Sent')
  received = transmitted('Received')
  [
    {label: "sent", data: sent},
    {label: "received", data: received},
  ].to_json
end

get '/messages.json' do
  content_type 'application/json'
  msg_data = common_query(:messages, :timestamp, :messages).map(&:values)
  [{label: 'Messages', data: msg_data}].to_json
end

get '/users.json' do
  content_type 'application/json'
  usr_data = common_query(:users, :timestamp, :users).map(&:values)
  [{label: 'Users', data: usr_data}].to_json
end

# FIXME: the nodes are real, but the edges are completely made up!
get '/tree.json' do
  content_type 'application/json'
  db_json = DB[:servers]
    .order_by(:timestamp.desc)
    .limit(1)
    .first[:servers]

  servers = JSON.parse(db_json).map.with_index { |name, i|
    {group: i, name: name}
  }

  edges = servers.map.with_index { |server, i|
    next if i.zero?
    {source: i - 1, target: i, value: 10}
  }.compact

  {nodes: servers, links: edges}.to_json
end

get '/channel.log' do
  content_type 'text/plain'

  start_time = Integer(params[:start])
  end_time   = Integer(params[:end])
  log_entries = DB[:channelogs]
    .where(:channel => params[:channel])
    .where(:timestamp => params[:start]..params[:end])
    .order_by(:timestamp)

  log_entries.inject("") do |log, entry|
    # TODO: include timestamp
    log << "#{entry[:nick]}: #{entry[:message]}\r\n"
  end
end

BEGIN {
  def common_query(table, *select_cols)
    DB[table]
      .select(*select_cols)
      .order_by(:timestamp.desc)
      .limit(50)
  end

  def transmitted(label)
    common_query(:transmitted, :timestamp, :bytes)
      .where(:label => label)
      .map(&:values)
  end
}
