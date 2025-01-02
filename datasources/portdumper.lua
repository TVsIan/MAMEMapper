outfile = io.open('ports.json', 'w')
outfile:write(string.format('{\n\t"%s":{\n', manager.machine.system.name))
lines = 0
for t, p in pairs(manager.machine.ioport.ports) do
    if (not string.match(t, ':DSW') and not string.match(t, ':TEST')) then
		for n, f in pairs(p.fields) do
			i =  manager.machine.ioport:input_type_to_token(f.type, f.player)
			if (string.match(i, 'P._') or string.match(i, 'COIN.') or string.match(i, 'START.')) then 
				if (lines == 0) then
					outfile:write(string.format('\t\t"%s":{"tag":"%s", "mask":"%i"}', i, t, f.mask))
				else
					outfile:write(string.format(',\n\t\t"%s":{"tag":"%s", "mask":"%i"}', i, t, f.mask))
				end
				lines = lines + 1
			end
		end
	end
end
outfile:write('\n\t}\n}')
outfile:close()
print(string.format('Dumped %i ports from %s', lines, manager.machine.system.name))
manager.machine:exit()