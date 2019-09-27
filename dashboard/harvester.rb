#!/usr/bin/env ruby

# collects data from the irked IRC daemon to display on the admin dashboard

require 'socket'
require 'time'
require 'sequel'
require 'json'


class Harvester
  def initialize(host = 'localhost', port = 6667)
    @host = host
    @port = port

    @db = Sequel.sqlite('dashboard.db')
    @db.create_table! :transmitted do
      primary_key :id
      Integer :timestamp
      Integer :bytes
      String  :label
    end
    [[:users, :users], [:messages, :messages]].each do |table, colname|
      @db.create_table! table do
        primary_key :id
        Integer :timestamp
        Integer colname
      end
    end
    @db.create_table! :servers do
      primary_key :id
      Integer :timestamp
      text :servers
    end

    @sent_recorded = StatsBuffer.new(50)
    @rcvd_recorded = StatsBuffer.new(50)
    @msgs_recorded = StatsBuffer.new(50)
  end

  def harvest
    @socket = TCPSocket.open @host, @port
    register
    loop do
      sent, rcvd = transmission_stats
      msgs = messages
      sent.reject! { |n, ts| @sent_recorded.include? ts }
      rcvd.reject! { |n, ts| @rcvd_recorded.include? ts }
      msgs.reject! { |n, ts| @msgs_recorded.include? ts }
      @db[:transmitted].import [:timestamp, :bytes, :label],
        sent.map { |n, ts| [ts, n, "Sent"] } +
        rcvd.map { |n, ts| [ts, n, "Received"] }
      @db[:messages].import [:messages, :timestamp], msgs
      @db[:users].insert [:users, :timestamp], users
      @db[:servers].insert [:servers, :timestamp], server_graph
      sent.each { |n, ts| @sent_recorded << ts }
      rcvd.each { |n, ts| @rcvd_recorded << ts }
      msgs.each { |n, ts| @msgs_recorded << ts }
      sleep 10
    end
  rescue Interrupt
  ensure
    @socket.puts "QUIT" if @socket
  end

  private

  def register
    @socket.puts "NICK harvester"
    @socket.puts "USER harvester 0 * :stats harvester"
    line = ""
    puts (line = @socket.gets) until line =~ / 376 /
  end

  def transmission_stats
    @socket.puts "STATS t"
    sent_stats_line = @socket.gets
    rcvd_stats_line = @socket.gets
    @socket.gets # end of stats
    sent = parse_stats(sent_stats_line)
    rcvd = parse_stats(rcvd_stats_line)
    [sent, rcvd]
  end

  def users
    @socket.puts 'LUSERS'
    rpl_251 = @socket.gets
    rpl_255 = @socket.gets
    while select [@socket], [], [], 0.1
      junk = @socket.gets
    end

    rpl_251 =~ /There are (\d+) users/
    num_users = $1.to_i
    [num_users, Time.now.to_i]
  end

  def messages
    @socket.puts 'STATS m'
    rpl_223 = @socket.gets
    @socket.gets # end of stats
    parse_stats(rpl_223)
  end

  def server_graph
    @socket.puts 'LINKS'
    servers = []
    while (server_line = @socket.gets) !~ /End of LINKS/
      p, c, _, h, server, *junk = server_line.split
      servers << server
    end
    [servers.to_json, Time.now.to_i]
  end

  def parse_stats(line)
    line.scan(/(?:([0-9a-f]+),([0-9a-f]+))/i).map { |n, ts|
      [n.to_i(16), ts.to_i(16)]
    }
  end
end

Harvester.new.harvest

BEGIN {
  class StatsBuffer
    include Enumerable

    def initialize(size)
      @size = size
      @arr  = []
    end

    def <<(e)
      @arr << e
      @arr.shift while @arr.size > @size
      e
    end

    def each
      @arr.each { |e| yield e }
    end
  end
}
